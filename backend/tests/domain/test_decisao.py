from app.domain.decisao import escolher
from app.domain.modelos import Criterios, Restricao
from tests.fabricas import prato


def test_alternativas_preferem_outros_restaurantes():
    ps = [
        prato(id="1", restaurante_id="r1"),
        prato(id="2", restaurante_id="r1"),
        prato(id="3", restaurante_id="r2"),
        prato(id="4", restaurante_id="r3"),
    ]
    e = escolher(ps, Criterios())
    assert e.principal.id == "1"
    assert [p.id for p in e.alternativas] == ["3", "4"]


def test_repete_restaurante_so_se_nao_houver_outra_opcao():
    ps = [
        prato(id="1", restaurante_id="r1"),
        prato(id="2", restaurante_id="r1"),
        prato(id="3", restaurante_id="r2"),
    ]
    e = escolher(ps, Criterios())
    assert [p.id for p in e.alternativas] == ["3", "2"]


def test_menos_de_tres_mostra_so_os_que_passam():
    e = escolher([prato(id="1")], Criterios())
    assert e.principal.id == "1" and e.alternativas == []


def test_nenhum_passa_devolve_principal_vazio():
    e = escolher([prato(atende=set())], Criterios(restricoes={Restricao.vegano}))
    assert e.principal is None and e.candidatos == [] and e.alternativas == []


def test_candidatos_ate_seis():
    ps = [prato(id=str(i)) for i in range(8)]
    e = escolher(ps, Criterios())
    assert [p.id for p in e.candidatos] == ["0", "1", "2", "3", "4", "5"]
