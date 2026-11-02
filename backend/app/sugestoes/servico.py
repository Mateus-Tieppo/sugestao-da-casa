"""Orquestra o pedido: agente com LLM e, se falhar, o modo demonstração."""

import asyncio
import logging
import time
from typing import Literal

from app.agente.agente import ResultadoAgente, rodar_agente
from app.cardapio.repositorio import Repositorio
from app.demo.interpretador import interpretar, rotulos
from app.demo.textos import diferenca, explicar, frase_decisao, mensagem_afrouxar
from app.domain.afrouxar import PropostaAfrouxar, propor_afrouxar
from app.domain.ajustes import aplicar_ajuste
from app.domain.decisao import Escolha, escolher
from app.domain.modelos import Criterios, Prato
from app.llm.cliente import ClienteLLM
from app.sugestoes.esquemas import (
    Etiqueta,
    MudancaSugerida,
    PedidoSugestao,
    PratoSugerido,
    PropostaSugerida,
    RespostaSugestao,
)

log = logging.getLogger("sugestoes")


class CardapioIndisponivel(Exception):
    """O repositório não conseguiu entregar o cardápio."""


class SugestaoIndisponivel(Exception):
    """Nem o modo demonstração conseguiu responder."""


def _etiquetas(prato: Prato, criterios: Criterios) -> list[str]:
    atendidas = Criterios(restricoes=criterios.restricoes & prato.atende)
    return [rotulo for _, rotulo in rotulos(atendidas)] + [f"{prato.tempo_min} min"]


def _sugerido(
    prato: Prato, criterios: Criterios, explicacao: str, dif: str | None
) -> PratoSugerido:
    return PratoSugerido(
        id=prato.id,
        nome=prato.nome,
        restaurante=prato.restaurante_nome,
        preco_centavos=prato.preco_centavos,
        taxa_entrega_centavos=prato.taxa_entrega_centavos,
        total_centavos=prato.total_centavos,
        tempo_min=prato.tempo_min,
        foto_url=prato.foto_url,
        etiquetas=_etiquetas(prato, criterios),
        explicacao=explicacao,
        diferenca=dif,
    )


def montar_resposta(
    modo: Literal["ia", "demonstracao"],
    criterios: Criterios,
    escolha: Escolha,
    proposta: PropostaAfrouxar | None,
    frase: str | None = None,
    explicacoes: dict[str, str] | None = None,
    diferencas: dict[str, str] | None = None,
) -> RespostaSugestao:
    """Único ponto que converte o domínio na resposta HTTP; texto ausente vira texto pronto."""
    explicacoes = explicacoes or {}
    diferencas = diferencas or {}
    principal = escolha.principal
    entendido = [Etiqueta(chave=k, rotulo=r) for k, r in rotulos(criterios)]

    if principal is None:
        sugerida = None
        if proposta is not None:
            sugerida = PropostaSugerida(
                mudancas=[MudancaSugerida(**m.model_dump()) for m in proposta.mudancas],
                mensagem=mensagem_afrouxar(proposta),
                prato=_sugerido(
                    proposta.prato,
                    criterios,
                    explicacoes.get(proposta.prato.id)
                    or explicar(proposta.prato, criterios),
                    None,
                ),
            )
        return RespostaSugestao(
            status="sem_resultado",
            modo=modo,
            criterios=criterios,
            entendido=entendido,
            frase_decisao=None,
            principal=None,
            alternativas=[],
            proposta=sugerida,
        )

    return RespostaSugestao(
        status="ok",
        modo=modo,
        criterios=criterios,
        entendido=entendido,
        frase_decisao=frase or frase_decisao(principal),
        principal=_sugerido(
            principal,
            criterios,
            explicacoes.get(principal.id) or explicar(principal, criterios),
            None,
        ),
        alternativas=[
            _sugerido(
                alt,
                criterios,
                explicacoes.get(alt.id) or explicar(alt, criterios),
                diferencas.get(alt.id) or diferenca(alt, principal),
            )
            for alt in escolha.alternativas
        ],
        proposta=None,
    )


def _resposta_do_agente(r: ResultadoAgente) -> RespostaSugestao:
    return montar_resposta(
        "ia",
        r.criterios,
        r.escolha,
        r.proposta,
        r.frase_decisao,
        r.explicacoes,
        r.diferencas,
    )


def _demonstracao(
    texto: str | None,
    atuais: Criterios | None,
    prato_atual: Prato | None,
    pratos: list[Prato],
) -> RespostaSugestao:
    if texto is not None:
        interpretacao = interpretar(texto, atuais)
        criterios = interpretacao.criterios
        if interpretacao.ajuste is not None and prato_atual is not None:
            criterios = aplicar_ajuste(criterios, interpretacao.ajuste, prato_atual)
    else:
        criterios = atuais or Criterios()
    escolha = escolher(pratos, criterios)
    proposta = propor_afrouxar(pratos, criterios) if escolha.principal is None else None
    return montar_resposta("demonstracao", criterios, escolha, proposta)


async def sugerir(
    pedido: PedidoSugestao, repo: Repositorio, llm: ClienteLLM, timeout_s: float
) -> RespostaSugestao:
    try:
        pratos = await repo.pratos()
    except Exception as e:
        # só a classe: a mensagem pode carregar dados do pedido ou credenciais
        log.warning("cardápio indisponível: %s", type(e).__name__)
        raise CardapioIndisponivel from e

    texto = (pedido.texto or "").strip() or None
    prato_atual = next((p for p in pratos if p.id == pedido.prato_atual_id), None)

    limite = time.monotonic() + timeout_s
    try:
        # teto de segurança para tudo; o passo 2 do agente tem prazo próprio, menor
        async with asyncio.timeout(timeout_s):
            resultado = await rodar_agente(
                texto, pedido.criterios, prato_atual, pratos, llm, limite
            )
        return _resposta_do_agente(resultado)
    except Exception as e:  # noqa: BLE001 - qualquer falha do LLM cai na demonstração
        log.warning("agente falhou, usando modo demonstração: %s", type(e).__name__)
    try:
        return _demonstracao(texto, pedido.criterios, prato_atual, pratos)
    except Exception as e:
        log.error("modo demonstração falhou: %s", type(e).__name__)
        raise SugestaoIndisponivel from e
