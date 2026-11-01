from app.domain.modelos import Criterios, Prato

EIXO_AUSENTE = 50
BONUS_DOCE = 100


def _normalizado(valor: int, valores: list[int]) -> float:
    """0 para o menor valor e 1 para o maior; 0 quando todos são iguais."""
    menor, maior = min(valores), max(valores)
    if menor == maior:
        return 0.0
    return (valor - menor) / (maior - menor)


def pontuar(prato: Prato, criterios: Criterios, todos: list[Prato]) -> float:
    pontos = 0.0
    for eixo, alvo in criterios.alvos.items():
        pontos += 100 - abs(prato.eixos.get(eixo, EIXO_AUSENTE) - alvo)
    if criterios.barato:
        totais = [p.total_centavos for p in todos]
        pontos += 100 * (1 - _normalizado(prato.total_centavos, totais))
    if criterios.rapido:
        tempos = [p.tempo_min for p in todos]
        pontos += 100 * (1 - _normalizado(prato.tempo_min, tempos))
    if criterios.quer_doce and prato.doce:
        pontos += BONUS_DOCE
    return pontos


def ranquear(pratos: list[Prato], criterios: Criterios) -> list[Prato]:
    return sorted(pratos, key=lambda p: (-pontuar(p, criterios, pratos), p.id))
