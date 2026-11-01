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
from app.domain.texto import normalizar
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


_PADRAO_NULO: dict[str, Any] = {
    "restricoes": [],
    "ingredientes_excluidos": [],
    "alvos": {},
    "barato": False,
    "rapido": False,
}


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
        return _PADRAO_NULO[info.field_name]

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
        orcamento_max_centavos=_limite(
            palavras.orcamento_max_centavos,
            args.orcamento_max_centavos,
            base.orcamento_max_centavos,
        ),
        tempo_max_min=_limite(
            palavras.tempo_max_min, args.tempo_max_min, base.tempo_max_min
        ),
        alvos={**base.alvos, **palavras.alvos, **args.alvos},
        barato=args.barato or palavras.barato or base.barato,
        rapido=args.rapido or palavras.rapido or base.rapido,
    )


def _limite(do_texto: int | None, do_llm: int | None, atual: int | None) -> int | None:
    """Número dito no texto vence; o LLM só pode apertar um limite, nunca afrouxar."""
    if do_texto is not None:
        return do_texto
    if do_llm is None:
        return atual
    if atual is None or do_llm <= atual:
        return do_llm
    return atual


def _resumo_prato(p: Prato) -> str:
    return (
        f"{p.nome} ({p.restaurante_nome}), {_reais(p.total_centavos)}, {p.tempo_min} min, "
        f"eixos { ({e.value: v for e, v in p.eixos.items()}) }"
    )


def _reais(centavos: int) -> str:
    return f"R$ {centavos / 100:.2f}".replace(".", ",")


def _apelidos(escolha: Escolha) -> dict[str, Prato]:
    """Ids curtos (p1..pN) mostrados ao modelo; ids reais nunca saem daqui."""
    return {f"p{i}": p for i, p in enumerate(escolha.candidatos, start=1)}


def _resolver(ref: Any, apelidos: dict[str, Prato]) -> Prato | None:
    if not isinstance(ref, str):
        return None
    achado = apelidos.get(ref.strip().lower())
    if achado is not None:
        return achado
    nome = normalizar(ref)
    return next((p for p in apelidos.values() if normalizar(p.nome) == nome), None)


def _tem_emoji(texto: str) -> bool:
    return any(
        ord(c) >= 0x1F000 or 0x2190 <= ord(c) <= 0x2BFF or ord(c) in (0xFE0F, 0x200D)
        for c in texto
    )


def _resultado_ferramenta(escolha: Escolha, criterios: Criterios) -> str:
    return json.dumps(
        {
            "criterios": criterios.model_dump(mode="json"),
            "candidatos": [
                {
                    "id": alias,
                    "nome": p.nome,
                    "restaurante": p.restaurante_nome,
                    "total_reais": round(p.total_centavos / 100, 2),
                    "tempo_min": p.tempo_min,
                    "eixos": {e.value: v for e, v in p.eixos.items()},
                    "ingredientes": p.ingredientes,
                }
                for alias, p in _apelidos(escolha).items()
            ],
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _texto_valido(valor: Any, limite: int) -> str | None:
    if (
        isinstance(valor, str)
        and valor.strip()
        and len(valor) <= limite
        and not _tem_emoji(valor)
    ):
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
    apelidos = _apelidos(escolha)
    principal = _resolver(dados.get("principal_id"), apelidos)
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
        alt = _resolver(alt_id, apelidos)
        if alt is None or alt.id == principal.id or alt in alternativas:
            continue
        alternativas.append(alt)
        diferencas_modelo[alt.id] = dif
    reserva = [escolha.principal, *escolha.alternativas, *escolha.candidatos]
    for alt in reserva:
        if alt is None:
            continue
        if len(alternativas) >= MAX_ALTERNATIVAS:
            break
        if alt.id != principal.id and alt not in alternativas:
            alternativas.append(alt)
    alternativas = alternativas[:MAX_ALTERNATIVAS]

    brutas_expl = dados.get("explicacoes", dados.get("explicações"))
    explicacoes_modelo: dict[str, Any] = {}
    for chave, texto in (brutas_expl if isinstance(brutas_expl, dict) else {}).items():
        dono = _resolver(chave, apelidos)
        if dono is not None:
            explicacoes_modelo[dono.id] = texto
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
    if frase and normalizar(principal.nome) not in normalizar(frase):
        frase = None
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
