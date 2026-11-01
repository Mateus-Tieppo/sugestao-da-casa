import math
from typing import Literal

from pydantic import BaseModel

from app.domain.filtro import filtrar
from app.domain.modelos import Criterios, Prato
from app.domain.ranking import ranquear

Campo = Literal["orcamento", "tempo"]


class Mudanca(BaseModel):
    campo: Campo
    valor_atual: int
    valor_sugerido: int


class PropostaAfrouxar(BaseModel):
    mudancas: list[Mudanca]  # 1 ou 2 itens, orçamento primeiro
    prato: Prato


def _aumento(m: Mudanca) -> float:
    if m.valor_atual == 0:
        return math.inf
    return m.valor_sugerido / m.valor_atual


def _arredondar_reais(centavos: int) -> int:
    return math.ceil(centavos / 100) * 100


def _melhor_com(
    pratos: list[Prato], criterios: Criterios, orcamento: int | None, tempo: int | None
) -> Prato:
    afrouxado = criterios.model_copy(
        update={"orcamento_max_centavos": orcamento, "tempo_max_min": tempo}
    )
    return ranquear(filtrar(pratos, afrouxado), afrouxado)[0]


def _proposta(
    campo: Campo,
    pratos: list[Prato],
    criterios: Criterios,
    atual: int | None,
) -> PropostaAfrouxar | None:
    """Menor valor do campo (mantendo o outro limite) que faz algum prato passar."""
    if atual is None:
        return None
    chave = "orcamento_max_centavos" if campo == "orcamento" else "tempo_max_min"
    sem_limite = criterios.model_copy(update={chave: None})
    elegiveis = filtrar(pratos, sem_limite)
    if not elegiveis:
        return None
    if campo == "orcamento":
        sugerido = _arredondar_reais(min(p.total_centavos for p in elegiveis))
    else:
        sugerido = min(p.tempo_min for p in elegiveis)
    if sugerido <= atual:
        return None  # já passaria: não há o que afrouxar neste campo
    if campo == "orcamento":
        melhor = _melhor_com(pratos, criterios, sugerido, criterios.tempo_max_min)
    else:
        melhor = _melhor_com(
            pratos, criterios, criterios.orcamento_max_centavos, sugerido
        )
    return PropostaAfrouxar(
        mudancas=[Mudanca(campo=campo, valor_atual=atual, valor_sugerido=sugerido)],
        prato=melhor,
    )


def _proposta_dupla(
    pratos: list[Prato], criterios: Criterios
) -> PropostaAfrouxar | None:
    """Menor par (orçamento, tempo) que faz algum prato passar; só com os dois limites."""
    orcamento, tempo = criterios.orcamento_max_centavos, criterios.tempo_max_min
    if orcamento is None or tempo is None:
        return None
    sem_limites = criterios.model_copy(
        update={"orcamento_max_centavos": None, "tempo_max_min": None}
    )
    opcoes: list[tuple[float, int, Mudanca, Mudanca]] = []
    for p in filtrar(pratos, sem_limites):
        m_orc = Mudanca(
            campo="orcamento",
            valor_atual=orcamento,
            valor_sugerido=_arredondar_reais(p.total_centavos),
        )
        m_tempo = Mudanca(campo="tempo", valor_atual=tempo, valor_sugerido=p.tempo_min)
        if m_orc.valor_sugerido <= orcamento or m_tempo.valor_sugerido <= tempo:
            continue  # um campo só já resolveria (e foi tentado antes)
        opcoes.append(
            (max(_aumento(m_orc), _aumento(m_tempo)), p.total_centavos, m_orc, m_tempo)
        )
    if not opcoes:
        return None
    _, _, m_orc, m_tempo = min(opcoes, key=lambda o: (o[0], o[1]))
    melhor = _melhor_com(
        pratos, criterios, m_orc.valor_sugerido, m_tempo.valor_sugerido
    )
    return PropostaAfrouxar(mudancas=[m_orc, m_tempo], prato=melhor)


def propor_afrouxar(
    pratos: list[Prato], criterios: Criterios
) -> PropostaAfrouxar | None:
    """Afrouxa apenas orçamento e/ou tempo; restrições e ingredientes excluídos ficam intactos.

    Prefere um campo só (menor aumento relativo); se nenhum sozinho resolve, os dois juntos.
    """
    unicas = [
        p
        for p in (
            _proposta("orcamento", pratos, criterios, criterios.orcamento_max_centavos),
            _proposta("tempo", pratos, criterios, criterios.tempo_max_min),
        )
        if p is not None
    ]
    if unicas:
        return min(unicas, key=lambda p: _aumento(p.mudancas[0]))  # empate: orçamento
    return _proposta_dupla(pratos, criterios)
