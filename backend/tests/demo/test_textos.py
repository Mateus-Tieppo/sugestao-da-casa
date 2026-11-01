from app.demo.textos import diferenca, explicar, frase_decisao, mensagem_afrouxar
from app.domain.afrouxar import Mudanca, PropostaAfrouxar
from app.domain.modelos import Criterios, Eixo, Restricao
from tests.fabricas import prato


def test_textos_nao_ficam_vazios_e_cabem():
    p = prato(nome="Caldo verde da Vó Lina")
    assert 0 < len(explicar(p, Criterios(alvos={Eixo.temperatura: 85}))) <= 160
    assert "Caldo verde" in frase_decisao(p)


def test_frase_decisao_artigo():
    assert (
        frase_decisao(prato(nome="Sopa de abóbora")) == "Hoje pede uma Sopa de abóbora."
    )
    assert (
        frase_decisao(prato(nome="Moqueca de peixe"))
        == "Hoje pede uma Moqueca de peixe."
    )
    assert (
        frase_decisao(prato(nome="Risoto de funghi"))
        == "Hoje pede um Risoto de funghi."
    )


def test_explicar_cita_ate_dois_motivos():
    c = Criterios(
        restricoes={Restricao.sem_lactose},
        alvos={Eixo.temperatura: 85, Eixo.peso: 25},
    )
    p = prato(
        eixos={Eixo.temperatura: 85, Eixo.peso: 20},
        atende={Restricao.sem_lactose},
    )
    t = explicar(p, c)
    assert "quentinho" in t and "leve" in t
    assert "sem lactose" not in t  # no máximo dois motivos
    assert len(t) <= 160


def test_explicar_sem_criterios_ainda_fala_algo():
    t = explicar(prato(), Criterios())
    assert t and len(t) <= 160


def test_explicar_com_restricao_e_orcamento():
    t = explicar(
        prato(),
        Criterios(restricoes={Restricao.sem_lactose}, orcamento_max_centavos=4000),
    )
    assert "sem lactose" in t and "R$ 40" in t


def _proposta(pr, *mudancas):
    return PropostaAfrouxar(mudancas=list(mudancas), prato=pr)


def test_mensagem_afrouxar_dois_campos():
    pr = prato(nome="Sopa de abóbora")
    m = mensagem_afrouxar(
        _proposta(
            pr,
            Mudanca(campo="orcamento", valor_atual=1500, valor_sugerido=1900),
            Mudanca(campo="tempo", valor_atual=10, valor_sugerido=15),
        )
    )
    assert (
        m
        == "Com tudo isso junto não achei nada, mas se subir para R$ 19 e der para esperar 15 min tem Sopa de abóbora."
    )


def test_mensagem_afrouxar_orcamento():
    pr = prato(nome="Sopa de abóbora")
    m = mensagem_afrouxar(
        _proposta(pr, Mudanca(campo="orcamento", valor_atual=2000, valor_sugerido=2200))
    )
    assert (
        m
        == "Com tudo isso junto não achei nada, mas se subir para R$ 22 tem Sopa de abóbora."
    )
    m = mensagem_afrouxar(
        _proposta(pr, Mudanca(campo="orcamento", valor_atual=2000, valor_sugerido=2250))
    )
    assert "R$ 22,50" in m


def test_mensagem_afrouxar_tempo():
    pr = prato(nome="Sopa de abóbora")
    m = mensagem_afrouxar(
        _proposta(pr, Mudanca(campo="tempo", valor_atual=20, valor_sugerido=35))
    )
    assert (
        m
        == "Com tudo isso junto não achei nada, mas se der para esperar 35 min tem Sopa de abóbora."
    )


def test_diferenca():
    base = prato(eixos={Eixo.peso: 60, Eixo.temperatura: 50, Eixo.picancia: 10})
    leve = prato(eixos={Eixo.peso: 20, Eixo.temperatura: 50, Eixo.picancia: 10})
    assert diferenca(leve, base) == "mais leve"
    assert diferenca(base, leve) == "mais caprichado"
    quente = prato(eixos={Eixo.peso: 60, Eixo.temperatura: 90, Eixo.picancia: 10})
    assert diferenca(quente, base) == "mais quentinho"
    assert diferenca(base, quente) == "mais fresco"
    picante = prato(eixos={Eixo.peso: 60, Eixo.temperatura: 50, Eixo.picancia: 70})
    assert diferenca(picante, base) == "um toque de picância"
    assert diferenca(base, picante) == "mais suave"
    barato = prato(preco_centavos=1500)
    assert diferenca(barato, prato(preco_centavos=3000)) == "mais em conta"
    rapido = prato(tempo_min=10)
    assert diferenca(rapido, prato(tempo_min=40)) == "chega mais rápido"
    assert diferenca(prato(), prato()) == "outra boa opção"
    assert len(diferenca(leve, base)) <= 40
