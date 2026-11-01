from app.domain.modelos import Criterios, Eixo
from app.domain.ranking import pontuar, ranquear
from tests.fabricas import prato


def test_quentinho_e_leve_vence():
    caldo = prato(id="caldo", eixos={Eixo.temperatura: 90, Eixo.peso: 25})
    salada = prato(id="salada", eixos={Eixo.temperatura: 10, Eixo.peso: 15})
    feijoada = prato(id="feijoada", eixos={Eixo.temperatura: 90, Eixo.peso: 95})
    c = Criterios(alvos={Eixo.temperatura: 85, Eixo.peso: 25})
    assert ranquear([salada, feijoada, caldo], c)[0].id == "caldo"


def test_barato_favorece_menor_total():
    caro, barato = prato(id="a", preco_centavos=6000), prato(id="b", preco_centavos=2000)
    assert ranquear([caro, barato], Criterios(barato=True))[0].id == "b"


def test_rapido_favorece_menor_tempo():
    lento, rapido = prato(id="a", tempo_min=60), prato(id="b", tempo_min=15)
    assert ranquear([lento, rapido], Criterios(rapido=True))[0].id == "b"


def test_desempate_deterministico_por_id():
    ps = [prato(id="b"), prato(id="a")]
    assert [p.id for p in ranquear(ps, Criterios())] == ["a", "b"]


def test_sem_preferencia_pontuacao_zero():
    p = prato()
    assert pontuar(p, Criterios(), [p]) == 0


def test_barato_com_minimo_igual_maximo_nao_divide_por_zero():
    ps = [prato(id="a"), prato(id="b")]
    assert pontuar(ps[0], Criterios(barato=True), ps) == 100


def test_eixo_ausente_no_prato_vale_50():
    p = prato(eixos={})
    assert pontuar(p, Criterios(alvos={Eixo.peso: 50}), [p]) == 100
    assert pontuar(p, Criterios(alvos={Eixo.peso: 0}), [p]) == 50
