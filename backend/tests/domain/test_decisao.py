from app.domain.decisao import escolher
from app.domain.modelos import Criterios, Eixo, Restricao
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


def test_doce_fora_quando_nao_pedido():
    salgado = prato(id="s", restaurante_id="r1", eixos={Eixo.temperatura: 10})
    sobremesa = prato(
        id="d", restaurante_id="r2", doce=True, eixos={Eixo.temperatura: 20}
    )
    c = Criterios(alvos={Eixo.temperatura: 20})
    e = escolher([salgado, sobremesa], c)
    assert e.principal.id == "s"
    assert all(not p.doce for p in e.candidatos + e.alternativas)
    assert escolher([sobremesa], c).principal is None


def test_doce_ganha_quando_pedido():
    salgado = prato(id="s", restaurante_id="r1", eixos={Eixo.temperatura: 20})
    sobremesa = prato(
        id="d", restaurante_id="r2", doce=True, eixos={Eixo.temperatura: 60}
    )
    c = Criterios(alvos={Eixo.temperatura: 20}, quer_doce=True)
    e = escolher([salgado, sobremesa], c)
    assert e.principal.id == "d"
    assert "s" in [p.id for p in e.candidatos]  # salgado continua possível


def test_afrouxar_ignora_doce_quando_nao_pedido():
    from app.domain.afrouxar import propor_afrouxar

    sobremesa = prato(id="d", doce=True, preco_centavos=1000)
    c = Criterios(orcamento_max_centavos=100)
    assert propor_afrouxar([sobremesa], c) is None
