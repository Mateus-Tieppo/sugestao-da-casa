"""Agente: o LLM interpreta e redige; o código filtra, ranqueia e garante as restrições."""

import json
from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator

from app.agente.prompts import FERRAMENTA_BUSCAR_PRATOS, PEDIDO_ESCRITA, SISTEMA
from app.demo.interpretador import interpretar
from app.demo.textos import diferenca, explicar, frase_decisao
from app.domain.afrouxar import PropostaAfrouxar, propor_afrouxar
from app.domain.ajustes import Ajuste, aplicar_ajuste
from app.domain.decisao import MAX_ALTERNATIVAS, Escolha, escolher
from app.domain.modelos import Criterios, Eixo, Prato, Restricao
from app.llm.cliente import ClienteLLM

LIMITE_EXPLICACAO_GUARDA = 200
LIMITE_DIFERENCA_GUARDA = 60
NOME_FERRAMENTA = "buscar_pratos"


class AgenteFalhou(Exception):
    """O modelo não entregou uma interpretação utilizável (passo 1)."""


class ResultadoAgente(BaseModel):
    criterios: Criterios
    escolha: Escolha
    proposta: PropostaAfrouxar | None
    frase_decisao: str | None
    explicacoes: dict[str, str]
    diferencas: dict[str, str]


class _Argumentos(BaseModel):
    restricoes: set[Restricao] = Field(default_factory=set)
    ingredientes_excluidos: set[str] = Field(default_factory=set)
    orcamento_max_centavos: int | None = None
    tempo_max_min: int | None = None
    alvos: dict[Eixo, int] = Field(default_factory=dict)
    barato: bool = False
    rapido: bool = False
    ajuste: Ajuste | None = None

    @field_validator(
        "restricoes",
        "ingredientes_excluidos",
        "alvos",
        "barato",
        "rapido",
        mode="before",
    )
    @classmethod
    def _nulo_vira_padrao(cls, valor: Any, info) -> Any:
        if valor is not None:
            return valor
        return {"barato": False, "rapido": False}.get(info.field_name, [])

    @field_validator("alvos")
    @classmethod
    def _alvos_em_faixa(cls, alvos: dict[Eixo, int]) -> dict[Eixo, int]:
        if any(not 0 <= v <= 100 for v in alvos.values()):
            raise ValueError("alvos devem ir de 0 a 100")
        return alvos


def _ler_argumentos(resposta_chamadas: list) -> _Argumentos:
    if not resposta_chamadas:
        raise AgenteFalhou("o modelo não chamou a ferramenta")
    chamada = resposta_chamadas[0]
    if chamada.nome != NOME_FERRAMENTA:
        raise AgenteFalhou(f"ferramenta desconhecida: {chamada.nome}")
    try:
        bruto = json.loads(chamada.argumentos)
        if not isinstance(bruto, dict):
            raise TypeError("argumentos não são um objeto")
        return _Argumentos.model_validate(bruto)
    except (ValueError, TypeError, ValidationError) as e:
        raise AgenteFalhou(f"argumentos inválidos: {e}") from e


def _mesclar(
    atuais: Criterios | None, args: _Argumentos, palavras: Criterios
) -> Criterios:
    base = atuais or Criterios()
    return Criterios(
        restricoes=base.restricoes | args.restricoes | palavras.restricoes,
        ingredientes_excluidos=(
            base.ingredientes_excluidos
            | args.ingredientes_excluidos
            | palavras.ingredientes_excluidos
        ),
        orcamento_max_centavos=_primeiro_nao_nulo(
            args.orcamento_max_centavos,
            palavras.orcamento_max_centavos,
            base.orcamento_max_centavos,
        ),
        tempo_max_min=_primeiro_nao_nulo(
            args.tempo_max_min, palavras.tempo_max_min, base.tempo_max_min
        ),
        alvos={**base.alvos, **palavras.alvos, **args.alvos},
        barato=args.barato or palavras.barato or base.barato,
        rapido=args.rapido or palavras.rapido or base.rapido,
    )


def _primeiro_nao_nulo(*valores: int | None) -> int | None:
    return next((v for v in valores if v is not None), None)


def _resumo_prato(p: Prato) -> str:
    return (
        f"{p.nome} ({p.restaurante_nome}), {_reais(p.total_centavos)}, {p.tempo_min} min, "
        f"eixos { ({e.value: v for e, v in p.eixos.items()}) }"
    )


def _reais(centavos: int) -> str:
    return f"R$ {centavos / 100:.2f}".replace(".", ",")


def _resultado_ferramenta(escolha: Escolha, criterios: Criterios) -> str:
    return json.dumps(
        {
            "criterios": criterios.model_dump(mode="json"),
            "candidatos": [
                {
                    "id": p.id,
                    "nome": p.nome,
                    "restaurante": p.restaurante_nome,
                    "total_reais": round(p.total_centavos / 100, 2),
                    "tempo_min": p.tempo_min,
                    "eixos": {e.value: v for e, v in p.eixos.items()},
                    "ingredientes": p.ingredientes,
                }
                for p in escolha.candidatos
            ],
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _texto_valido(valor: Any, limite: int) -> str | None:
    if isinstance(valor, str) and valor.strip() and len(valor) <= limite:
        return valor
    return None


def _ler_escrita(conteudo: str | None) -> dict:
    """Passo 2 nunca derruba o fluxo: qualquer defeito vira dict vazio (textos prontos)."""
    try:
        dados = json.loads(conteudo or "")
    except ValueError:
        return {}
    return dados if isinstance(dados, dict) else {}


def _guardar(escolha: Escolha, criterios: Criterios, dados: dict) -> ResultadoAgente:
    """Só prato de escolha.candidatos sai daqui; o que o modelo errar vira texto pronto."""
    candidatos = {p.id: p for p in escolha.candidatos}
    pedido = dados.get("principal_id")
    principal = candidatos.get(pedido) if isinstance(pedido, str) else None
    modelo_acertou = principal is not None
    if principal is None:
        principal = escolha.principal
    assert principal is not None

    alternativas: list[Prato] = []
    diferencas_modelo: dict[str, Any] = {}
    brutas = dados.get("alternativas")
    for item in brutas if isinstance(brutas, list) else []:
        if isinstance(item, dict):
            alt_id, dif = item.get("id"), item.get("diferenca")
        else:
            alt_id, dif = item, None
        alt = candidatos.get(alt_id) if isinstance(alt_id, str) else None
        if alt is None or alt.id == principal.id or alt in alternativas:
            continue
        alternativas.append(alt)
        diferencas_modelo[alt.id] = dif
    for alt in escolha.alternativas:
        if len(alternativas) >= MAX_ALTERNATIVAS:
            break
        if alt.id != principal.id and alt not in alternativas:
            alternativas.append(alt)
    alternativas = alternativas[:MAX_ALTERNATIVAS]

    brutas_expl = dados.get("explicacoes", dados.get("explicações"))
    explicacoes_modelo = brutas_expl if isinstance(brutas_expl, dict) else {}
    explicacoes: dict[str, str] = {}
    for p in [principal, *alternativas]:
        texto = _texto_valido(explicacoes_modelo.get(p.id), LIMITE_EXPLICACAO_GUARDA)
        explicacoes[p.id] = texto or explicar(p, criterios)
    if not modelo_acertou:
        explicacoes[principal.id] = explicar(principal, criterios)

    frase = (
        _texto_valido(dados.get("frase_decisao"), LIMITE_EXPLICACAO_GUARDA)
        if modelo_acertou
        else None
    )
    diferencas = {
        alt.id: _texto_valido(diferencas_modelo.get(alt.id), LIMITE_DIFERENCA_GUARDA)
        or diferenca(alt, principal)
        for alt in alternativas
    }
    return ResultadoAgente(
        criterios=criterios,
        escolha=Escolha(
            principal=principal,
            alternativas=alternativas,
            candidatos=escolha.candidatos,
        ),
        proposta=None,
        frase_decisao=frase or frase_decisao(principal),
        explicacoes=explicacoes,
        diferencas=diferencas,
    )


async def rodar_agente(
    texto: str | None,
    atuais: Criterios | None,
    prato_atual: Prato | None,
    pratos: list[Prato],
    llm: ClienteLLM,
) -> ResultadoAgente:
    mensagens: list[dict] = [{"role": "system", "content": SISTEMA}]

    if texto is not None:
        mensagens.append(
            {
                "role": "user",
                "content": (
                    f"Critérios atuais: {(atuais or Criterios()).model_dump_json()}\n"
                    f"Prato atual: {_resumo_prato(prato_atual) if prato_atual else 'nenhum'}\n"
                    f"Pedido: {texto}"
                ),
            }
        )
        resposta = await llm.conversar(
            mensagens, ferramentas=[FERRAMENTA_BUSCAR_PRATOS]
        )
        args = _ler_argumentos(resposta.chamadas)
        palavras = interpretar(texto, None)
        criterios = _mesclar(atuais, args, palavras.criterios)
        ajuste = args.ajuste or palavras.ajuste
        if ajuste is not None and prato_atual is not None:
            criterios = aplicar_ajuste(criterios, ajuste, prato_atual)
        chamada = resposta.chamadas[0]
        mensagens.append(
            {
                "role": "assistant",
                "content": resposta.conteudo,
                "tool_calls": [
                    {
                        "id": chamada.id,
                        "type": "function",
                        "function": {
                            "name": chamada.nome,
                            "arguments": chamada.argumentos,
                        },
                    }
                ],
            }
        )
    else:
        criterios = atuais or Criterios()

    escolha = escolher(pratos, criterios)
    if escolha.principal is None:
        return ResultadoAgente(
            criterios=criterios,
            escolha=escolha,
            proposta=propor_afrouxar(pratos, criterios),
            frase_decisao=None,
            explicacoes={},
            diferencas={},
        )

    resultado = _resultado_ferramenta(escolha, criterios)
    if texto is not None:
        mensagens.append(
            {"role": "tool", "tool_call_id": chamada.id, "content": resultado}
        )
        mensagens.append({"role": "user", "content": PEDIDO_ESCRITA})
    else:
        mensagens.append(
            {
                "role": "user",
                "content": f"Resultado da busca: {resultado}\n{PEDIDO_ESCRITA}",
            }
        )
    escrita = await llm.conversar(mensagens, json=True)
    return _guardar(escolha, criterios, _ler_escrita(escrita.conteudo))
