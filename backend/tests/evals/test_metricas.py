import json

import pytest

from app.domain.modelos import Criterios, Eixo, Restricao
from app.llm.cliente import ChamadaFerramenta, RespostaLLM
from evals.metricas import criterios_cobrem, percentil, resumir
from evals.rodar import avaliar_frase
from tests.agente.llm_falso import LLMRoteirizado
from tests.fabricas import prato

SL = Restricao.sem_lactose
SG = Restricao.sem_gluten


def test_percentil_interpola_e_cobre_bordas():
    assert percentil([1, 2, 3, 4], 50) == 2.5
    assert percentil([5], 95) == 5
    assert percentil([1, 2, 3, 4, 5], 95) == pytest.approx(4.8)
    assert percentil([], 50) is None


def test_criterios_cobrem_restricoes_exigem_superconjunto():
    esperado = {"restricoes": ["sem_lactose"]}
    assert criterios_cobrem(esperado, Criterios(restricoes={SL, SG}))
    assert not criterios_cobrem(esperado, Criterios(restricoes={SG}))
    assert not criterios_cobrem(esperado, Criterios())


def test_criterios_cobrem_numeros_exatos_e_ausentes_nao_exigem_nada():
    esperado = {"orcamento_max_centavos": 3500, "tempo_max_min": 30}
    assert criterios_cobrem(
        esperado, Criterios(orcamento_max_centavos=3500, tempo_max_min=30)
    )
    assert not criterios_cobrem(
        esperado, Criterios(orcamento_max_centavos=4000, tempo_max_min=30)
    )
    assert not criterios_cobrem(esperado, Criterios(tempo_max_min=30))
    assert criterios_cobrem({}, Criterios(tempo_max_min=10))


def test_criterios_cobrem_excluidos_superconjunto():
    esperado = {"ingredientes_excluidos": ["cebola"]}
    assert criterios_cobrem(
        esperado, Criterios(ingredientes_excluidos={"cebola", "alho"})
    )
    assert not criterios_cobrem(esperado, Criterios(ingredientes_excluidos={"alho"}))


def test_resumir_agrega_taxas_e_latencias():
    linhas = [
        {"ok_passo1": True, "restricoes_corretas": True, "guarda_ok": True,
         "escolha_modelo": True, "latencia_s": 1.0},
        {"ok_passo1": True, "restricoes_corretas": False, "guarda_ok": True,
         "escolha_modelo": False, "latencia_s": 3.0},
        {"ok_passo1": False, "restricoes_corretas": False, "guarda_ok": None,
         "escolha_modelo": None, "latencia_s": 2.0},
        {"ok_passo1": True, "restricoes_corretas": True, "guarda_ok": True,
         "escolha_modelo": None, "latencia_s": 4.0},  # sem prato: não conta na escolha
    ]  # fmt: skip
    r = resumir(linhas)
    assert r["sucesso_passo1_pct"] == 75.0
    assert r["restricoes_corretas_pct"] == 50.0
    assert r["guarda_100"] is True
    assert r["escolha_modelo_pct"] == 50.0
    assert r["latencia_p50_s"] == 2.5


def test_resumir_guarda_quebrada_detectada():
    linhas = [
        {"ok_passo1": True, "restricoes_corretas": True, "guarda_ok": False,
         "escolha_modelo": True, "latencia_s": 1.0},
    ]  # fmt: skip
    assert resumir(linhas)["guarda_100"] is False


def _busca(**args) -> RespostaLLM:
    return RespostaLLM(
        chamadas=[ChamadaFerramenta(nome="buscar_pratos", argumentos=json.dumps(args))]
    )


def _pratos():
    return [
        prato(id="a", nome="Sopa", restaurante_id="r1", atende={SL},
              eixos={Eixo.temperatura: 90}),
        prato(id="b", nome="Risoto", restaurante_id="r2", atende={SL},
              eixos={Eixo.temperatura: 70}),
        prato(id="c", nome="Pizza", restaurante_id="r3", atende=set()),
    ]  # fmt: skip


async def test_avaliar_frase_sucesso_com_escolha_do_modelo():
    llm = LLMRoteirizado(
        [
            _busca(restricoes=["sem_lactose"]),
            RespostaLLM(conteudo='{"principal_id": "p2"}'),
        ]
    )
    frase = {"texto": "sem lactose", "restricoes": ["sem_lactose"]}
    r = await avaliar_frase(frase, _pratos(), llm)
    assert r["ok_passo1"] and r["restricoes_corretas"] and r["guarda_ok"]
    assert r["escolha_modelo"] is True
    assert r["latencia_s"] >= 0


async def test_avaliar_frase_escolha_invalida_nao_conta_como_do_modelo():
    llm = LLMRoteirizado(
        [
            _busca(restricoes=["sem_lactose"]),
            RespostaLLM(conteudo='{"principal_id": "zzz"}'),
        ]
    )
    r = await avaliar_frase(
        {"texto": "sem lactose", "restricoes": ["sem_lactose"]}, _pratos(), llm
    )
    assert r["ok_passo1"] and r["guarda_ok"]
    assert r["escolha_modelo"] is False


async def test_avaliar_frase_registra_falha_do_passo1_sem_levantar():
    llm = LLMRoteirizado([RespostaLLM(conteudo="oi")])  # sem chamar a ferramenta
    r = await avaliar_frase(
        {"texto": "sem lactose", "restricoes": ["sem_lactose"]}, _pratos(), llm
    )
    assert r["ok_passo1"] is False
    assert r["restricoes_corretas"] is False
    assert r["erro"]


async def test_avaliar_frase_registra_excecao_do_llm():
    llm = LLMRoteirizado([TimeoutError("lento")])
    r = await avaliar_frase({"texto": "x"}, _pratos(), llm)
    assert r["ok_passo1"] is False
    assert "TimeoutError" in r["erro"]
