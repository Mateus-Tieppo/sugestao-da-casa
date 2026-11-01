from app.domain.modelos import Criterios, Prato
from app.domain.texto import palavras


def _ingrediente_excluido(prato: Prato, excluidos: set[str]) -> bool:
    """Casa quando o excluído aparece como palavra(s) dentro de algum ingrediente."""
    for ingrediente in prato.ingredientes:
        do_prato = palavras(ingrediente)
        for excluido in excluidos:
            alvo = palavras(excluido)
            if not alvo:
                continue
            n = len(alvo)
            if any(do_prato[i : i + n] == alvo for i in range(len(do_prato) - n + 1)):
                return True
    return False


def passa_restricoes(prato: Prato, criterios: Criterios) -> bool:
    if not criterios.restricoes <= prato.atende:
        return False
    if (
        criterios.orcamento_max_centavos is not None
        and prato.total_centavos > criterios.orcamento_max_centavos
    ):
        return False
    if (
        criterios.tempo_max_min is not None
        and prato.tempo_min > criterios.tempo_max_min
    ):
        return False
    excluidos = criterios.ingredientes_excluidos
    return not (excluidos and _ingrediente_excluido(prato, excluidos))


def filtrar(pratos: list[Prato], criterios: Criterios) -> list[Prato]:
    return [p for p in pratos if passa_restricoes(p, criterios)]
