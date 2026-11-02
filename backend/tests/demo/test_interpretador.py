import pytest

from app.demo.interpretador import interpretar, remover, rotulos
from app.domain.ajustes import Ajuste
from app.domain.modelos import Criterios, Eixo, Restricao


def test_frase_do_exemplo():
    i = interpretar("algo quentinho, não muito pesado, até R$40, sem lactose", None)
    c = i.criterios
    assert c.restricoes == {Restricao.sem_lactose}
    assert c.orcamento_max_centavos == 4000
    assert c.alvos[Eixo.temperatura] == 85 and c.alvos[Eixo.peso] == 25


def test_sem_cebola_vira_ingrediente_excluido():
    assert interpretar("sem cebola", None).criterios.ingredientes_excluidos == {
        "cebola"
    }


def test_acumula_sobre_criterios_atuais():
    atuais = Criterios(restricoes={Restricao.sem_lactose})
    i = interpretar("mais barato", atuais)
    assert i.ajuste == Ajuste.mais_barato and i.criterios.restricoes == {
        Restricao.sem_lactose
    }


def test_segundo_exemplo_da_tela_inicial():
    c = interpretar("quero algo fresquinho e rápido, sem glúten", None).criterios
    assert c.restricoes == {Restricao.sem_gluten}
    assert c.alvos[Eixo.temperatura] == 20 and c.rapido


def test_menos_gorduroso_e_mais_leve():
    assert interpretar("algo menos gorduroso", None).ajuste == Ajuste.mais_leve


def test_rotulos_e_remover_sao_inversos():
    c = Criterios(restricoes={Restricao.sem_lactose}, orcamento_max_centavos=4000)
    assert ("orcamento", "até R$\u00a040") in rotulos(c)
    assert remover(c, "orcamento").orcamento_max_centavos is None
    assert remover(c, "restricao:sem_lactose").restricoes == set()


def test_negacao_vence_positivo():
    c = interpretar("não muito pesado", None).criterios
    assert c.alvos[Eixo.peso] == 25
    assert interpretar("nao pesado", None).criterios.alvos[Eixo.peso] == 25


def test_pesado_positivo():
    assert interpretar("quero algo bem pesado", None).criterios.alvos[Eixo.peso] == 80


def test_sem_pimenta_e_picancia_baixa():
    c = interpretar("sem pimenta", None).criterios
    assert c.alvos[Eixo.picancia] == 15
    assert c.ingredientes_excluidos == {"pimenta"}
    assert interpretar("não picante", None).criterios.alvos[Eixo.picancia] == 15


def test_picante_positivo():
    assert interpretar("algo apimentado", None).criterios.alvos[Eixo.picancia] == 75


def test_restricoes_nunca_viram_ingrediente():
    c = interpretar(
        "sem lactose, sem glúten, sem amendoim, sem frutos do mar, sem camarão, sem ovo",
        None,
    ).criterios
    assert c.ingredientes_excluidos == set()
    assert c.restricoes == {
        Restricao.sem_lactose,
        Restricao.sem_gluten,
        Restricao.sem_amendoim,
        Restricao.sem_frutos_do_mar,
        Restricao.sem_ovo,
    }


def test_vegano_vegetariano():
    assert interpretar("sou vegana", None).criterios.restricoes == {Restricao.vegano}
    assert interpretar("vegetariano", None).criterios.restricoes == {
        Restricao.vegetariano
    }


def test_ajustes_nao_viram_preferencias():
    i = interpretar("mais leve", None)
    assert i.ajuste == Ajuste.mais_leve and i.criterios.alvos == {}
    i = interpretar("mais barato", None)
    assert i.criterios.barato is False
    i = interpretar("mais rápido", None)
    assert i.criterios.rapido is False and i.ajuste == Ajuste.mais_rapido
    i = interpretar("mais quente", None)
    assert i.ajuste == Ajuste.mais_quente and i.criterios.alvos == {}
    i = interpretar("mais fresco", None)
    assert i.ajuste == Ajuste.mais_fresco and i.criterios.alvos == {}
    i = interpretar("menos picante", None)
    assert i.ajuste == Ajuste.menos_picante and i.criterios.alvos == {}
    i = interpretar("mais picante", None)
    assert i.ajuste == Ajuste.mais_picante and i.criterios.alvos == {}


def test_apenas_um_ajuste_o_primeiro():
    assert interpretar("mais barato e mais rápido", None).ajuste == Ajuste.mais_barato


def test_sem_ajuste_e_none():
    assert interpretar("quentinho", None).ajuste is None


def test_orcamento_tempo_e_atalhos():
    c = interpretar("máximo R$ 25,00? ate 30 min", None).criterios
    assert c.tempo_max_min == 30
    c = interpretar("até 35 reais", None).criterios
    assert c.orcamento_max_centavos == 3500
    c = interpretar("algo barato e com pressa", None).criterios
    assert c.barato and c.rapido
    assert interpretar("sopa", None).criterios.alvos[Eixo.temperatura] == 85
    assert interpretar("algo reconfortante", None).criterios.alvos[Eixo.conforto] == 85
    assert interpretar("matar a fome", None).criterios.alvos[Eixo.peso] == 80


def test_acumulacao_uniao_e_sobrescrita_so_se_mencionado():
    atuais = Criterios(
        restricoes={Restricao.sem_lactose},
        ingredientes_excluidos={"cebola"},
        orcamento_max_centavos=4000,
        tempo_max_min=30,
        alvos={Eixo.temperatura: 85, Eixo.peso: 25},
        barato=True,
    )
    c = interpretar("sem glúten, sem alho, até R$ 20, fresquinho", atuais).criterios
    assert c.restricoes == {Restricao.sem_lactose, Restricao.sem_gluten}
    assert c.ingredientes_excluidos == {"cebola", "alho"}
    assert c.orcamento_max_centavos == 2000
    assert c.tempo_max_min == 30
    assert c.alvos == {Eixo.temperatura: 20, Eixo.peso: 25}
    assert c.barato
    assert atuais.orcamento_max_centavos == 4000  # entrada não é mutada


def test_rotulos_ordem_deterministica():
    c = Criterios(
        restricoes={Restricao.sem_lactose},
        ingredientes_excluidos={"cebola"},
        orcamento_max_centavos=4000,
        tempo_max_min=30,
        alvos={
            Eixo.conforto: 85,
            Eixo.picancia: 15,
            Eixo.peso: 25,
            Eixo.temperatura: 85,
        },
        barato=True,
        rapido=True,
    )
    assert rotulos(c) == [
        ("restricao:sem_lactose", "sem lactose"),
        ("excluir:cebola", "sem cebola"),
        ("orcamento", "até R$\u00a040"),
        ("tempo", "até 30 min"),
        ("alvo:temperatura", "quentinho"),
        ("alvo:peso", "leve"),
        ("alvo:picancia", "sem picância"),
        ("alvo:conforto", "reconfortante"),
        ("barato", "barato"),
        ("rapido", "rápido"),
    ]


def test_rotulos_alternativos():
    c = Criterios(alvos={Eixo.temperatura: 20, Eixo.peso: 80, Eixo.picancia: 75})
    assert [r for _, r in rotulos(c)] == ["fresco", "caprichado", "picante"]


def test_remover_cada_chave():
    c = Criterios(
        ingredientes_excluidos={"cebola", "alho"},
        tempo_max_min=30,
        alvos={Eixo.peso: 25, Eixo.temperatura: 85},
        barato=True,
        rapido=True,
    )
    assert remover(c, "excluir:cebola").ingredientes_excluidos == {"alho"}
    assert remover(c, "tempo").tempo_max_min is None
    assert remover(c, "alvo:peso").alvos == {Eixo.temperatura: 85}
    assert remover(c, "barato").barato is False
    assert remover(c, "rapido").rapido is False
    assert remover(c, "inexistente") == c
    assert c.tempo_max_min == 30  # não muta


def test_detecta_doce():
    assert interpretar("uma sobremesa de chocolate", None).criterios.quer_doce
    assert interpretar("quero um brigadeiro", None).criterios.quer_doce
    assert interpretar("algo com açúcar", None).criterios.quer_doce
    assert not interpretar("algo quentinho", None).criterios.quer_doce


def test_doce_mantem_o_que_ja_estava():
    atuais = Criterios(quer_doce=True)
    assert interpretar("sem cebola", atuais).criterios.quer_doce


def test_rotulo_e_remover_doce():
    c = Criterios(rapido=True, barato=True, quer_doce=True)
    assert rotulos(c)[-3:] == [
        ("barato", "barato"),
        ("rapido", "rápido"),
        ("doce", "algo doce"),
    ]
    assert remover(c, "doce").quer_doce is False
    assert c.quer_doce


@pytest.mark.parametrize(
    "texto",
    ["quero batata-doce", "bowl de batata doce", "batata doce assada", "algo quentinho"],
)
def test_batata_doce_nao_e_sobremesa(texto):
    assert interpretar(texto, None).criterios.quer_doce is False


@pytest.mark.parametrize(
    "texto",
    ["quero doce de leite", "um doce", "sobremesa", "brigadeiro", "quero doces"],
)
def test_palavras_de_doce(texto):
    assert interpretar(texto, None).criterios.quer_doce is True


@pytest.mark.parametrize(
    "texto", ["sem doce", "não quero doce", "nada doce", "nao quero nenhum doce"]
)
def test_negacao_de_doce(texto):
    assert interpretar(texto, None).criterios.quer_doce is False
    atuais = Criterios(quer_doce=True)
    c = interpretar(texto, atuais).criterios
    assert c.quer_doce is False
    assert "doce" not in c.ingredientes_excluidos


@pytest.mark.parametrize(
    "texto",
    [
        "um lanche para até 2 pessoas",
        "chocolate 70%",
        "até 3 unidades",
        "até 2 porções",
        "forno a 180 graus",
    ],
)
def test_numero_com_outra_unidade_nao_vira_orcamento(texto):
    assert interpretar(texto, None).criterios.orcamento_max_centavos is None


def test_orcamento_com_e_sem_simbolo():
    assert interpretar("até 40", None).criterios.orcamento_max_centavos == 4000
    assert interpretar("até R$ 40", None).criterios.orcamento_max_centavos == 4000
    assert interpretar("até 40 reais", None).criterios.orcamento_max_centavos == 4000
    assert interpretar("até 40 contos", None).criterios.orcamento_max_centavos == 4000


def test_ate_30_min_so_tempo():
    c = interpretar("até 30 min", None).criterios
    assert c.tempo_max_min == 30 and c.orcamento_max_centavos is None


@pytest.mark.parametrize("texto", ["sem carne", "não como carne", "nada de carne"])
def test_sem_carne_vira_vegetariano(texto):
    c = interpretar(texto, None).criterios
    assert Restricao.vegetariano in c.restricoes
    assert "carne" not in c.ingredientes_excluidos


def test_sem_pimenta_vira_alvo_e_exclusao():
    c = interpretar("sem pimenta", None).criterios
    assert c.alvos[Eixo.picancia] == 15
    assert "pimenta" in c.ingredientes_excluidos


def test_rotulo_de_orcamento_nao_quebra_linha():
    c = interpretar("até 40", None).criterios
    assert ("orcamento", "até R$ 40") in rotulos(c)


@pytest.mark.parametrize(
    ("texto", "restricao"),
    [
        ("nada de frutos do mar hoje, até 50 reais", Restricao.sem_frutos_do_mar),
        ("não como frutos do mar", Restricao.sem_frutos_do_mar),
        ("sou alérgico a camarão", Restricao.sem_frutos_do_mar),
        ("tenho alergia a frutos do mar", Restricao.sem_frutos_do_mar),
        ("nada de lactose", Restricao.sem_lactose),
        ("não posso comer glúten", Restricao.sem_gluten),
        ("sou alérgica a amendoim", Restricao.sem_amendoim),
        ("nada de ovo", Restricao.sem_ovo),
    ],
)
def test_restricao_com_outras_formas_de_negar(texto, restricao):
    c = interpretar(texto, None).criterios
    assert restricao in c.restricoes
    assert c.ingredientes_excluidos == set()
