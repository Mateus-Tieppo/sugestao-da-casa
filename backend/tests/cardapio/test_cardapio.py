"""Cobertura e consistência do cardápio (supabase/cardapio.json)."""

import json
import re
from pathlib import Path

import pytest

from app.domain.modelos import Eixo, Restricao

RAIZ = Path(__file__).resolve().parents[3] / "supabase"
CARDAPIO = RAIZ / "cardapio.json"


@pytest.fixture(scope="module")
def dados():
    return json.loads(CARDAPIO.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def itens(dados):
    """(restaurante, prato) para cada prato."""
    return [(r, p) for r in dados["restaurantes"] for p in r["pratos"]]


def total(r, p):
    return p["preco_centavos"] + r["taxa_entrega_centavos"]


def tempo(r, p):
    return r["tempo_entrega_min"] + p["tempo_preparo_min"]


def test_tamanho(dados, itens):
    assert len(dados["restaurantes"]) >= 12
    assert len(itens) >= 70
    ids = [p["id"] for _, p in itens] + [r["id"] for r in dados["restaurantes"]]
    assert len(set(ids)) == len(ids)


@pytest.mark.parametrize("restricao", list(Restricao))
def test_cada_restricao_tem_ao_menos_8_pratos(itens, restricao):
    assert sum(restricao.value in p["atende"] for _, p in itens) >= 8


def test_atende_so_tem_restricoes_validas(itens):
    validas = {r.value for r in Restricao}
    for _, p in itens:
        assert set(p["atende"]) <= validas, p["nome"]


def test_totais_cobrem_14_a_75_reais(itens):
    totais = [total(r, p) for r, p in itens]
    assert 1400 <= min(totais) <= 1600
    assert 7000 <= max(totais) <= 7500


def test_tempos_cobrem_15_a_60_minutos(itens):
    tempos = [tempo(r, p) for r, p in itens]
    assert 15 <= min(tempos) <= 20
    assert 55 <= max(tempos) <= 60


@pytest.mark.parametrize("eixo", list(Eixo))
def test_eixos_vao_de_um_extremo_ao_outro(itens, eixo):
    valores = [p[eixo.value] for _, p in itens if p[eixo.value] is not None]
    assert all(0 <= v <= 100 for v in valores)
    assert min(valores) <= 15
    assert max(valores) >= 85


def test_pratos_do_mockup(itens):
    por_nome = {p["nome"]: (r, p) for r, p in itens}
    _, caldo = por_nome["Caldo verde da Vó Lina"]
    assert caldo["preco_centavos"] == 3200
    assert "sem_lactose" in caldo["atende"]
    assert caldo["temperatura"] == 90
    assert caldo["peso"] == 25
    assert por_nome["Lámen shoyu leve"][1]["preco_centavos"] == 3800
    assert por_nome["Curry de coco"][1]["preco_centavos"] == 3600


def test_existe_bowl_vegano_sem_gluten_de_17_a_22(itens):
    achados = [
        p["nome"]
        for r, p in itens
        if {"vegano", "sem_gluten"} <= set(p["atende"])
        and 1700 <= total(r, p) <= 2200
        and "bowl" in p["nome"].lower()
    ]
    assert achados


# Palavras que terminam em "s" mas já estão no singular.
INVARIAVEIS = {"brócolis", "picles"}


def test_ingredientes_minusculos_e_no_singular(itens):
    for _, p in itens:
        assert p["ingredientes"], p["nome"]
        for ing in p["ingredientes"]:
            assert ing == ing.lower().strip(), (p["nome"], ing)
            assert ing not in {"ovos", "tomates", "camarões", "legumes"}, ing
            primeira = ing.split()[0]
            assert not primeira.endswith("s") or primeira in INVARIAVEIS, (
                p["nome"],
                ing,
            )


LATICINIOS = [
    "queijo", "leite", "manteiga", "creme de leite", "requeijão", "iogurte",
    "cream cheese", "catupiry", "mussarela", "muçarela", "parmesao", "parmesão",
    "cheddar", "gorgonzola", "provolone", "coalhada", "doce de leite",
    "leite condensado", "chantilly", "ricota", "burrata", "nata", "leite de vaca",
]  # fmt: skip
GLUTEN = [
    "trigo", "farinha de trigo", "pão", "pao", "macarrão", "macarrao", "massa",
    "shoyu", "cerveja", "cuscuz marroquino", "tortilha de trigo", "crouton",
    "croûton", "farinha de rosca", "empanado",
]  # fmt: skip
AMENDOIM = ["amendoim", "paçoca", "pacoca", "granola"]
OVO = ["ovo", "maionese", "gema", "massa fresca", "nhoque"]
PEIXES = [
    "salmão", "atum", "tilápia", "bacalhau", "peixe", "anchova", "sardinha",
    "robalo", "kani",
]  # fmt: skip
CRUSTACEOS_MOLUSCOS = [
    "camarão", "lula", "polvo", "siri", "caranguejo", "mexilhão", "ostra",
    "lagosta", "marisco",
]  # fmt: skip
CARNES = [
    "frango", "carne", "bacon", "linguiça", "porco", "costela", "charque", "presunto",
    "peixe", "salmão", "atum", "tilápia", "camarão", "lula", "polvo", "mexilhão",
    "bacalhau", "calabresa", "cordeiro", "sardinha", "salsicha",
]  # fmt: skip


def _tem(ingredientes, palavras):
    for ing in ingredientes:
        ing = re.sub(r"leite de (coco|amêndoa|aveia)", "", ing)
        for pal in palavras:
            if re.search(rf"\b{pal}\b", ing):
                return True
    return False


def test_restricoes_consistentes_com_ingredientes(itens):
    for _, p in itens:
        ing, at = p["ingredientes"], set(p["atende"])
        if "sem_lactose" in at:
            assert not _tem(ing, LATICINIOS), p["nome"]
        if "sem_ovo" in at:
            assert not _tem(ing, OVO), p["nome"]
        if "sem_gluten" in at:
            assert not _tem(ing, GLUTEN), p["nome"]
        if "sem_amendoim" in at:
            assert not _tem(ing, AMENDOIM), p["nome"]
        if "sem_frutos_do_mar" in at:
            assert not _tem(ing, PEIXES + CRUSTACEOS_MOLUSCOS), p["nome"]
        if "vegetariano" in at:
            assert not _tem(ing, CARNES), p["nome"]
        if "vegano" in at:
            assert {"vegetariano", "sem_lactose", "sem_ovo"} <= at, p["nome"]
            assert not _tem(ing, CARNES + LATICINIOS + ["ovo", "maionese", "mel"]), p[
                "nome"
            ]


def test_seed_sql_esta_atualizado():
    import importlib.util

    spec = importlib.util.spec_from_file_location("gerar_seed", RAIZ / "gerar_seed.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    esperado = modulo.gerar(json.loads(CARDAPIO.read_text(encoding="utf-8")))
    assert (RAIZ / "seed.sql").read_text(encoding="utf-8") == esperado, (
        "rode: python supabase/gerar_seed.py"
    )


def test_doces_marcados(itens):
    assert all(isinstance(p.get("doce"), bool) for _, p in itens)
    doces = {p["nome"] for _, p in itens if p["doce"]}
    assert len(doces) >= 5
    for r, p in itens:
        if r["nome"] == "Doceria Açúcar & Afeto":
            assert p["doce"], p["nome"]
    assert "Bowl de açaí com granola" in doces
    assert "Pé de moleque caseiro" in doces
    assert "Caldo verde da Vó Lina" not in doces
