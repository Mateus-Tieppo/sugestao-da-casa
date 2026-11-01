from pydantic import BaseModel

from app.domain.filtro import filtrar
from app.domain.modelos import Criterios, Prato
from app.domain.ranking import ranquear

MAX_CANDIDATOS = 6
MAX_ALTERNATIVAS = 2


class Escolha(BaseModel):
    principal: Prato | None
    alternativas: list[Prato]
    candidatos: list[Prato]


def _alternativas(principal: Prato, restantes: list[Prato]) -> list[Prato]:
    """Próximas do ranking, preferindo restaurantes ainda não usados."""
    escolhidas: list[Prato] = []
    usados = {principal.restaurante_id}
    for p in restantes:
        if len(escolhidas) == MAX_ALTERNATIVAS:
            break
        if p.restaurante_id not in usados:
            escolhidas.append(p)
            usados.add(p.restaurante_id)
    for p in restantes:
        if len(escolhidas) == MAX_ALTERNATIVAS:
            break
        if p not in escolhidas:
            escolhidas.append(p)
    return escolhidas


def escolher(pratos: list[Prato], criterios: Criterios) -> Escolha:
    ranking = ranquear(filtrar(pratos, criterios), criterios)
    if not ranking:
        return Escolha(principal=None, alternativas=[], candidatos=[])
    principal, restantes = ranking[0], ranking[1:]
    return Escolha(
        principal=principal,
        alternativas=_alternativas(principal, restantes),
        candidatos=ranking[:MAX_CANDIDATOS],
    )
