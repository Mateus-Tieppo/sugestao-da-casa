import math
from typing import Literal

from pydantic import BaseModel

from app.domain.filtro import filtrar
from app.domain.modelos import Criterios, Prato
from app.domain.ranking import ranquear


class PropostaAfrouxar(BaseModel):
    campo: Literal["orcamento", "tempo"]
    valor_atual: int
    valor_sugerido: int
    prato: Prato


def _razao(proposta: PropostaAfrouxar) -> float:
    if proposta.valor_atual == 0:
        return math.inf
    return proposta.valor_sugerido / proposta.valor_atual


def _proposta(
    campo: Literal["orcamento", "tempo"],
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
        sugerido = math.ceil(min(p.total_centavos for p in elegiveis) / 100) * 100
    else:
        sugerido = min(p.tempo_min for p in elegiveis)
    if sugerido <= atual:
        return None  # já passaria: não há o que afrouxar neste campo
    afrouxado = criterios.model_copy(update={chave: sugerido})
    melhor = ranquear(filtrar(pratos, afrouxado), afrouxado)[0]
    return PropostaAfrouxar(
        campo=campo, valor_atual=atual, valor_sugerido=sugerido, prato=melhor
    )


def propor_afrouxar(pratos: list[Prato], criterios: Criterios) -> PropostaAfrouxar | None:
    """Afrouxa apenas orçamento ou tempo; restrições e ingredientes excluídos ficam intactos."""
    propostas = [
        p
        for p in (
            _proposta("orcamento", pratos, criterios, criterios.orcamento_max_centavos),
            _proposta("tempo", pratos, criterios, criterios.tempo_max_min),
        )
        if p is not None
    ]
    if not propostas:
        return None
    return min(propostas, key=_razao)  # min é estável: empate fica com orçamento
