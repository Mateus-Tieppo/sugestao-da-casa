from app.domain.filtro import filtrar, passa_restricoes
from app.domain.modelos import Criterios, Eixo, Restricao
from tests.fabricas import prato


def test_exige_todas_as_restricoes():
    p = prato(atende={Restricao.sem_lactose})
    assert passa_restricoes(p, Criterios(restricoes={Restricao.sem_lactose}))
    assert not passa_restricoes(
        p, Criterios(restricoes={Restricao.sem_lactose, Restricao.vegano})
    )


def test_orcamento_inclui_taxa_de_entrega():
    p = prato(preco_centavos=3500, taxa_entrega_centavos=600)
    assert not passa_restricoes(p, Criterios(orcamento_max_centavos=4000))
    assert passa_restricoes(p, Criterios(orcamento_max_centavos=4100))


def test_tempo_maximo_e_inclusivo():
    assert passa_restricoes(prato(tempo_min=30), Criterios(tempo_max_min=30))
    assert not passa_restricoes(prato(tempo_min=31), Criterios(tempo_max_min=30))


def test_ingrediente_excluido_ignora_acento_e_caixa():
    p = prato(ingredientes=["Cebola roxa", "tomate"])
    assert not passa_restricoes(p, Criterios(ingredientes_excluidos={"cebola"}))


def test_ingrediente_excluido_com_acento_no_prato_e_no_criterio():
    p = prato(ingredientes=["Açúcar mascavo", "Pão"])
    assert not passa_restricoes(p, Criterios(ingredientes_excluidos={"acucar"}))
    assert not passa_restricoes(p, Criterios(ingredientes_excluidos={"Pão"}))


def test_ingrediente_excluido_casa_palavra_inteira():
    p = prato(ingredientes=["cebolinha"])
    assert passa_restricoes(p, Criterios(ingredientes_excluidos={"cebola"}))


def test_preferencias_nao_eliminam():
    assert passa_restricoes(
        prato(eixos={Eixo.peso: 90}), Criterios(alvos={Eixo.peso: 10}, barato=True)
    )


def test_total_centavos_soma_preco_e_taxa():
    assert prato(preco_centavos=3500, taxa_entrega_centavos=600).total_centavos == 4100


def test_filtrar_mantem_ordem_e_remove_reprovados():
    a = prato(id="a", tempo_min=20)
    b = prato(id="b", tempo_min=50)
    c = prato(id="c", tempo_min=30)
    assert [p.id for p in filtrar([a, b, c], Criterios(tempo_max_min=30))] == ["a", "c"]


def test_criterios_padrao_aprova_tudo():
    assert passa_restricoes(prato(), Criterios())
