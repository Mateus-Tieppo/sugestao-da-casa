from app.domain.afrouxar import propor_afrouxar
from app.domain.modelos import Criterios, Eixo, Restricao
from tests.fabricas import prato


def test_propoe_subir_orcamento_minimo():
    bowl = prato(
        id="bowl",
        atende={Restricao.vegano},
        preco_centavos=1700,
        taxa_entrega_centavos=500,
        tempo_min=20,
    )
    c = Criterios(restricoes={Restricao.vegano}, orcamento_max_centavos=1500)
    p = propor_afrouxar([bowl], c)
    assert [(m.campo, m.valor_sugerido) for m in p.mudancas] == [("orcamento", 2200)]
    assert p.prato.id == "bowl"


def test_arredonda_orcamento_para_cima_ao_real():
    p1 = prato(preco_centavos=1701, taxa_entrega_centavos=0)
    p = propor_afrouxar([p1], Criterios(orcamento_max_centavos=1500))
    m = p.mudancas[0]
    assert m.valor_sugerido == 1800 and m.valor_atual == 1500


def test_nunca_afrouxa_restricao_alimentar():
    carne = prato(atende=set(), preco_centavos=1000)
    assert (
        propor_afrouxar(
            [carne],
            Criterios(restricoes={Restricao.vegano}, orcamento_max_centavos=1500),
        )
        is None
    )


def test_nunca_afrouxa_ingrediente_excluido():
    p = prato(ingredientes=["cebola"], tempo_min=50)
    assert (
        propor_afrouxar(
            [p], Criterios(ingredientes_excluidos={"cebola"}, tempo_max_min=30)
        )
        is None
    )


def test_escolhe_menor_aumento_relativo():
    caro = prato(id="caro", preco_centavos=3000, taxa_entrega_centavos=0, tempo_min=20)
    demorado = prato(
        id="demorado", preco_centavos=1000, taxa_entrega_centavos=0, tempo_min=35
    )
    p = propor_afrouxar(
        [caro, demorado], Criterios(orcamento_max_centavos=1500, tempo_max_min=30)
    )
    assert [(m.campo, m.valor_sugerido) for m in p.mudancas] == [("tempo", 35)]
    assert p.prato.id == "demorado"


def test_empate_prefere_orcamento():
    # orçamento 1000 -> 2000 (2x); tempo 30 -> 60 (2x)
    caro = prato(id="caro", preco_centavos=2000, taxa_entrega_centavos=0, tempo_min=10)
    lento = prato(id="lento", preco_centavos=500, taxa_entrega_centavos=0, tempo_min=60)
    p = propor_afrouxar(
        [caro, lento], Criterios(orcamento_max_centavos=1000, tempo_max_min=30)
    )
    assert [(m.campo, m.valor_sugerido) for m in p.mudancas] == [("orcamento", 2000)]


def test_sem_criterio_numerico_definido_devolve_none():
    assert propor_afrouxar([prato()], Criterios()) is None


def test_so_propoe_campo_definido():
    lento = prato(tempo_min=60)
    p = propor_afrouxar([lento], Criterios(tempo_max_min=30))
    assert [(m.campo, m.valor_sugerido) for m in p.mudancas] == [("tempo", 60)]
    caro = prato(preco_centavos=5000, taxa_entrega_centavos=0)
    p = propor_afrouxar([caro], Criterios(orcamento_max_centavos=1000))
    assert [m.campo for m in p.mudancas] == ["orcamento"]


def test_propoe_os_dois_campos_quando_um_so_nao_resolve():
    p1 = prato(preco_centavos=3000, taxa_entrega_centavos=0, tempo_min=60)
    c = Criterios(orcamento_max_centavos=1000, tempo_max_min=30)
    p = propor_afrouxar([p1], c)
    assert [(m.campo, m.valor_atual, m.valor_sugerido) for m in p.mudancas] == [
        ("orcamento", 1000, 3000),
        ("tempo", 30, 60),
    ]


def test_dois_campos_minimiza_o_maior_aumento_relativo():
    # caro: orç 4x, tempo 1x->(tempo 40/30); equilibrado: orç 2x, tempo 2x
    a = prato(id="a", preco_centavos=4000, taxa_entrega_centavos=0, tempo_min=31)
    b = prato(id="b", preco_centavos=2000, taxa_entrega_centavos=0, tempo_min=50)
    c = Criterios(orcamento_max_centavos=1000, tempo_max_min=30)
    assert propor_afrouxar([a, b], c).prato.id == "b"


def test_dois_campos_empate_fica_com_o_mais_barato():
    a = prato(id="a", preco_centavos=3000, taxa_entrega_centavos=0, tempo_min=60)
    b = prato(id="b", preco_centavos=2000, taxa_entrega_centavos=0, tempo_min=60)
    c = Criterios(orcamento_max_centavos=1000, tempo_max_min=30)
    # razões: a=3x, b=2x vs tempo 2x: b vence já pelo maior; teste de desempate abaixo
    assert propor_afrouxar([a, b], c).prato.id == "b"
    b2 = prato(id="b2", preco_centavos=2000, taxa_entrega_centavos=0, tempo_min=60)
    c2 = prato(id="c2", preco_centavos=1900, taxa_entrega_centavos=0, tempo_min=60)
    assert propor_afrouxar([b2, c2], c).prato.id == "c2"


def test_dois_campos_nao_afrouxa_restricao():
    carne = prato(atende=set(), preco_centavos=3000, tempo_min=60)
    c = Criterios(
        restricoes={Restricao.vegano}, orcamento_max_centavos=1000, tempo_max_min=30
    )
    assert propor_afrouxar([carne], c) is None


def test_dois_campos_exige_os_dois_limites_definidos():
    p1 = prato(preco_centavos=3000, taxa_entrega_centavos=0, tempo_min=60)
    assert (
        propor_afrouxar([p1], Criterios(orcamento_max_centavos=1000)).mudancas[0].campo
        == "orcamento"
    )
    assert (
        propor_afrouxar(
            [p1], Criterios(ingredientes_excluidos={"arroz"}, tempo_max_min=30)
        )
        is None
    )


def test_prato_e_o_melhor_do_ranking_com_o_valor_sugerido():
    leve = prato(
        id="leve",
        preco_centavos=1000,
        taxa_entrega_centavos=0,
        tempo_min=40,
        eixos={Eixo.peso: 10},
    )
    pesado = prato(
        id="pesado",
        preco_centavos=1000,
        taxa_entrega_centavos=0,
        tempo_min=40,
        eixos={Eixo.peso: 90},
    )
    c = Criterios(tempo_max_min=30, alvos={Eixo.peso: 90})
    p = propor_afrouxar([leve, pesado], c)
    assert p.mudancas[0].valor_sugerido == 40 and p.prato.id == "pesado"


def test_valor_atual_zero_nao_quebra():
    p1 = prato(preco_centavos=500, taxa_entrega_centavos=0, tempo_min=10)
    p = propor_afrouxar([p1], Criterios(orcamento_max_centavos=0))
    assert p.mudancas[0].valor_sugerido == 500
