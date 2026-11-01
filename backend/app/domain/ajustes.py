from enum import StrEnum

from app.domain.modelos import Criterios, Eixo, Prato
from app.domain.ranking import EIXO_AUSENTE

PASSO_EIXO = 25
PASSO_ORCAMENTO_CENTAVOS = 100
PASSO_TEMPO_MIN = 5


class Ajuste(StrEnum):
    mais_barato = "mais_barato"
    mais_rapido = "mais_rapido"
    mais_leve = "mais_leve"
    mais_quente = "mais_quente"
    mais_fresco = "mais_fresco"
    menos_picante = "menos_picante"
    mais_picante = "mais_picante"


# ajuste -> (eixo, sentido)
_EIXOS: dict[Ajuste, tuple[Eixo, int]] = {
    Ajuste.mais_leve: (Eixo.peso, -1),
    Ajuste.mais_quente: (Eixo.temperatura, 1),
    Ajuste.mais_fresco: (Eixo.temperatura, -1),
    Ajuste.menos_picante: (Eixo.picancia, -1),
    Ajuste.mais_picante: (Eixo.picancia, 1),
}


def aplicar_ajuste(criterios: Criterios, ajuste: Ajuste, prato_atual: Prato) -> Criterios:
    """Devolve novos critérios com o ajuste relativo ao prato atual; não muta a entrada."""
    if ajuste is Ajuste.mais_barato:
        orcamento = max(0, prato_atual.total_centavos - PASSO_ORCAMENTO_CENTAVOS)
        return criterios.model_copy(update={"orcamento_max_centavos": orcamento})
    if ajuste is Ajuste.mais_rapido:
        tempo = max(1, prato_atual.tempo_min - PASSO_TEMPO_MIN)
        return criterios.model_copy(update={"tempo_max_min": tempo})
    eixo, sentido = _EIXOS[ajuste]
    base = prato_atual.eixos.get(eixo, EIXO_AUSENTE)
    alvo = min(100, max(0, base + sentido * PASSO_EIXO))
    return criterios.model_copy(update={"alvos": {**criterios.alvos, eixo: alvo}})
