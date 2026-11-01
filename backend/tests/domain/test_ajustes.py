from app.domain.ajustes import Ajuste, aplicar_ajuste
from app.domain.modelos import Criterios, Eixo, Restricao
from tests.fabricas import prato


def test_mais_barato_e_relativo_ao_prato_atual_e_preserva_resto():
    atual = prato(preco_centavos=3200, taxa_entrega_centavos=500)
    c = aplicar_ajuste(Criterios(restricoes={Restricao.sem_lactose}), Ajuste.mais_barato, atual)
    assert c.orcamento_max_centavos == 3600 and c.restricoes == {Restricao.sem_lactose}


def test_mais_barato_nao_fica_negativo():
    atual = prato(preco_centavos=50, taxa_entrega_centavos=0)
    assert aplicar_ajuste(Criterios(), Ajuste.mais_barato, atual).orcamento_max_centavos == 0


def test_mais_rapido():
    atual = prato(tempo_min=40)
    assert aplicar_ajuste(Criterios(), Ajuste.mais_rapido, atual).tempo_max_min == 35


def test_mais_rapido_minimo_um():
    atual = prato(tempo_min=3)
    assert aplicar_ajuste(Criterios(), Ajuste.mais_rapido, atual).tempo_max_min == 1


def test_mais_leve_limita_em_zero():
    atual = prato(eixos={Eixo.peso: 10})
    assert aplicar_ajuste(Criterios(), Ajuste.mais_leve, atual).alvos[Eixo.peso] == 0


def test_eixos_relativos_e_limitados():
    atual = prato(eixos={Eixo.temperatura: 90, Eixo.picancia: 10})
    q = aplicar_ajuste(Criterios(), Ajuste.mais_quente, atual)
    assert q.alvos[Eixo.temperatura] == 100
    f = aplicar_ajuste(Criterios(), Ajuste.mais_fresco, atual)
    assert f.alvos[Eixo.temperatura] == 65
    assert aplicar_ajuste(Criterios(), Ajuste.mais_picante, atual).alvos[Eixo.picancia] == 35
    assert aplicar_ajuste(Criterios(), Ajuste.menos_picante, atual).alvos[Eixo.picancia] == 0


def test_eixo_ausente_conta_como_50():
    atual = prato(eixos={})
    assert aplicar_ajuste(Criterios(), Ajuste.mais_leve, atual).alvos[Eixo.peso] == 25


def test_nao_muta_entrada_e_preserva_outros_alvos():
    c = Criterios(alvos={Eixo.conforto: 80}, orcamento_max_centavos=9999)
    atual = prato(eixos={Eixo.peso: 60})
    novo = aplicar_ajuste(c, Ajuste.mais_leve, atual)
    assert c.alvos == {Eixo.conforto: 80} and c.orcamento_max_centavos == 9999
    assert novo.alvos == {Eixo.conforto: 80, Eixo.peso: 35}
    assert novo.orcamento_max_centavos == 9999
