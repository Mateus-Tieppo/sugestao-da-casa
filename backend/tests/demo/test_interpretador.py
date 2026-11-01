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
    assert ("orcamento", "até R$ 40") in rotulos(c)
    assert remover(c, "orcamento").orcamento_max_centavos is None
    assert remover(c, "restricao:sem_lactose").restricoes == set()


def test_negacao_vence_positivo():
    c = interpretar("não muito pesado", None).criterios
    assert c.alvos[Eixo.peso] == 25
    assert interpretar("nao pesado", None).criterios.alvos[Eixo.peso] == 25


def test_pesado_positivo():
    assert interpretar("quero algo bem pesado", None).criterios.alvos[Eixo.peso] == 80


def test_sem_pimenta_e_picancia_baixa_nao_ingrediente():
    c = interpretar("sem pimenta", None).criterios
    assert c.alvos[Eixo.picancia] == 15
    assert c.ingredientes_excluidos == set()
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
        ("orcamento", "até R$ 40"),
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
