"""Funções puras de métrica da avaliação de provedores."""

from typing import Any

from app.domain.modelos import Criterios


def percentil(valores: list[float], p: float) -> float | None:
    """Percentil por interpolação linear (p de 0 a 100); None se não há valores."""
    if not valores:
        return None
    ordenados = sorted(valores)
    posicao = (len(ordenados) - 1) * p / 100
    baixo = int(posicao)
    alto = min(baixo + 1, len(ordenados) - 1)
    return ordenados[baixo] + (ordenados[alto] - ordenados[baixo]) * (posicao - baixo)


def criterios_cobrem(esperado: dict[str, Any], criterios: Criterios) -> bool:
    """Todas as restrições duras esperadas estão nos critérios finais.

    Restrições e ingredientes excluídos: superconjunto. Orçamento e tempo: igualdade.
    Campos que a frase não declara não são exigidos.
    """
    if not set(esperado.get("restricoes", [])) <= {
        r.value for r in criterios.restricoes
    }:
        return False
    if (
        not set(esperado.get("ingredientes_excluidos", []))
        <= criterios.ingredientes_excluidos
    ):
        return False
    for campo in ("orcamento_max_centavos", "tempo_max_min"):
        if campo in esperado and getattr(criterios, campo) != esperado[campo]:
            return False
    return True


def _pct(parte: int, total: int) -> float | None:
    return round(100 * parte / total, 1) if total else None


def resumir(linhas: list[dict[str, Any]]) -> dict[str, Any]:
    """Agrega os resultados por frase.

    - sucesso_passo1_pct e restricoes_corretas_pct: sobre todas as frases
      (falha conta como erro).
    - guarda_100: nenhum prato fora das restrições entre as frases que terminaram.
    - escolha_modelo_pct: sobre as frases em que houve prato e o passo 2 terminou.
    """
    n = len(linhas)
    guardas = [l["guarda_ok"] for l in linhas if l.get("guarda_ok") is not None]
    escolhas = [
        l["escolha_modelo"] for l in linhas if l.get("escolha_modelo") is not None
    ]
    latencias = [l["latencia_s"] for l in linhas]
    return {
        "frases": n,
        "sucesso_passo1_pct": _pct(sum(1 for l in linhas if l["ok_passo1"]), n),
        "restricoes_corretas_pct": _pct(
            sum(1 for l in linhas if l["restricoes_corretas"]), n
        ),
        "guarda_100": all(guardas),
        "escolha_modelo_pct": _pct(sum(1 for e in escolhas if e), len(escolhas)),
        "latencia_p50_s": percentil(latencias, 50),
        "latencia_p95_s": percentil(latencias, 95),
    }
