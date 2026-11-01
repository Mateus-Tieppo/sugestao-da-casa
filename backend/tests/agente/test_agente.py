import json

import pytest

from app.agente.agente import AgenteFalhou, rodar_agente
from app.demo.textos import explicar, frase_decisao
from app.domain.decisao import escolher
from app.domain.filtro import passa_restricoes
from app.domain.modelos import Criterios, Eixo, Restricao
from app.llm.cliente import ChamadaFerramenta, RespostaLLM
from tests.agente.llm_falso import LLMRoteirizado
from tests.fabricas import prato

SL = Restricao.sem_lactose


def _pratos():
    return [
        prato(id="a", nome="Sopa de abóbora", restaurante_id="r1", atende={SL},
              eixos={Eixo.temperatura: 90}, preco_centavos=2500),
        prato(id="b", nome="Risoto de cogumelos", restaurante_id="r2", atende={SL},
              eixos={Eixo.temperatura: 70}, preco_centavos=3200),
        prato(id="c", nome="Lasanha", restaurante_id="r3", atende={SL},
              eixos={Eixo.temperatura: 60}, preco_centavos=3600),
        prato(id="d", nome="Pizza de queijo", restaurante_id="r4", atende=set(),
              eixos={Eixo.temperatura: 90}, preco_centavos=2000),
    ]  # fmt: skip


def _busca(**args) -> RespostaLLM:
    return RespostaLLM(
        chamadas=[ChamadaFerramenta(nome="buscar_pratos", argumentos=json.dumps(args))]
    )


def _escrita(**campos) -> RespostaLLM:
    return RespostaLLM(conteudo=json.dumps(campos))


async def test_fluxo_feliz_usa_ferramenta_e_escolha_do_modelo():
    pratos = _pratos()
    esperado = escolher(pratos, Criterios(restricoes={SL}))
    cand = esperado.candidatos
    llm = LLMRoteirizado(
        [
            _busca(restricoes=["sem_lactose"]),
            _escrita(
                principal_id=cand[1].id,
                alternativas=[{"id": cand[0].id, "diferenca": "mais quentinho"}],
                frase_decisao="Hoje pede o segundo.",
                explicacoes={cand[1].id: "Combina com o que você pediu."},
            ),
        ]
    )
    r = await rodar_agente("algo sem lactose", None, None, pratos, llm)
    assert r.escolha.principal == cand[1]
    assert r.criterios.restricoes == {SL}
    assert r.frase_decisao == "Hoje pede o segundo."
    assert r.explicacoes[cand[1].id] == "Combina com o que você pediu."
    assert r.diferencas[cand[0].id] == "mais quentinho"
    assert llm.ferramentas_recebidas[0] is not None
    assert llm.json_recebido == [False, True]


async def test_guarda_descarta_prato_fora_dos_candidatos():
    pratos = _pratos()
    llm = LLMRoteirizado(
        [
            _busca(restricoes=["sem_lactose"]),
            _escrita(
                principal_id="d",  # tem lactose
                alternativas=[{"id": "d", "diferenca": "x"}],
                frase_decisao="Pizza!",
                explicacoes={"d": "Pizza é ótima."},
            ),
        ]
    )
    r = await rodar_agente("sem lactose", None, None, pratos, llm)
    esperado = escolher(pratos, Criterios(restricoes={SL}))
    assert r.escolha.principal == esperado.principal
    finais = [r.escolha.principal, *r.escolha.alternativas]
    assert all(passa_restricoes(p, r.criterios) for p in finais)
    assert "d" not in {p.id for p in finais}
    assert "d" not in r.explicacoes
    assert r.frase_decisao == frase_decisao(esperado.principal)
    assert r.explicacoes[esperado.principal.id] == explicar(
        esperado.principal, r.criterios
    )


async def test_argumentos_invalidos_lancam_agente_falhou():
    llm = LLMRoteirizado(
        [
            RespostaLLM(
                chamadas=[
                    ChamadaFerramenta(nome="buscar_pratos", argumentos="{nao e json")
                ]
            )
        ]
    )
    with pytest.raises(AgenteFalhou):
        await rodar_agente("oi", None, None, _pratos(), llm)


@pytest.mark.parametrize(
    "resposta",
    [
        RespostaLLM(conteudo="não sei"),
        RespostaLLM(chamadas=[ChamadaFerramenta(nome="outra", argumentos="{}")]),
        _busca(restricoes=["inexistente"]),
    ],
)
async def test_falhas_do_passo_1_lancam_agente_falhou(resposta):
    with pytest.raises(AgenteFalhou):
        await rodar_agente("oi", None, None, _pratos(), LLMRoteirizado([resposta]))


async def test_sem_texto_pula_interpretacao():
    pratos = _pratos()
    llm = LLMRoteirizado([_escrita(principal_id="a", alternativas=[], explicacoes={})])
    r = await rodar_agente(None, Criterios(restricoes={SL}), None, pratos, llm)
    assert len(llm.mensagens_recebidas) == 1
    assert llm.ferramentas_recebidas == [None]
    assert llm.json_recebido == [True]
    assert r.escolha.principal.id == "a"


async def test_ajuste_mais_barato_aplicado_ao_prato_atual():
    pratos = _pratos()
    atual = pratos[2]
    llm = LLMRoteirizado([_busca(ajuste="mais_barato"), _escrita(principal_id="a")])
    r = await rodar_agente(
        "mais barato", Criterios(restricoes={SL}), atual, pratos, llm
    )
    assert r.criterios.orcamento_max_centavos == atual.total_centavos - 100


async def test_sem_resultado_traz_proposta():
    pratos = _pratos()
    llm = LLMRoteirizado([_busca(orcamento_max_centavos=1000)])
    r = await rodar_agente("até 10 reais", None, None, pratos, llm)
    assert r.escolha.principal is None
    assert r.proposta is not None
    assert r.frase_decisao is None
    assert r.explicacoes == {} and r.diferencas == {}
    assert len(llm.mensagens_recebidas) == 1  # sem passo de escrita


async def test_merge_mantem_sem_lactose_quando_llm_esquece():
    atuais = Criterios(restricoes={SL}, ingredientes_excluidos={"cebola"})
    llm = LLMRoteirizado([_busca(restricoes=[]), _escrita(principal_id="a")])
    r = await rodar_agente("algo quentinho", atuais, None, _pratos(), llm)
    assert r.criterios.restricoes == {SL}
    assert r.criterios.ingredientes_excluidos == {"cebola"}


async def test_rede_de_palavras_chave_adiciona_restricao_perdida():
    llm = LLMRoteirizado([_busca(), _escrita(principal_id="a")])
    r = await rodar_agente("quero algo sem glúten", None, None, _pratos(), llm)
    assert Restricao.sem_gluten in r.criterios.restricoes


async def test_valor_do_llm_vence_o_das_palavras_chave():
    llm = LLMRoteirizado([_busca(tempo_max_min=20, barato=True)])
    r = await rodar_agente(
        "até 45 min", Criterios(tempo_max_min=60), None, _pratos(), llm
    )
    assert r.criterios.tempo_max_min == 20
    assert r.criterios.barato is True


async def test_passo_2_com_json_invalido_cai_para_textos_prontos():
    pratos = _pratos()
    llm = LLMRoteirizado(
        [_busca(restricoes=["sem_lactose"]), RespostaLLM(conteudo="{quebrado")]
    )
    r = await rodar_agente("sem lactose", None, None, pratos, llm)
    esperado = escolher(pratos, Criterios(restricoes={SL}))
    assert r.escolha.principal == esperado.principal
    assert r.frase_decisao == frase_decisao(esperado.principal)
    assert set(r.explicacoes) == {
        p.id for p in [esperado.principal, *esperado.alternativas]
    }


async def test_explicacao_longa_ou_vazia_vira_texto_pronto():
    pratos = _pratos()
    esperado = escolher(pratos, Criterios(restricoes={SL}))
    p, alt = esperado.principal, esperado.alternativas[0]
    llm = LLMRoteirizado(
        [
            _busca(restricoes=["sem_lactose"]),
            _escrita(
                principal_id=p.id,
                alternativas=[{"id": alt.id, "diferenca": ""}],
                explicacoes={p.id: "x" * 201, alt.id: "  "},
            ),
        ]
    )
    r = await rodar_agente("sem lactose", None, None, pratos, llm)
    assert r.explicacoes[p.id] == explicar(p, r.criterios)
    assert r.explicacoes[alt.id] == explicar(alt, r.criterios)


async def test_excecao_do_cliente_propaga():
    llm = LLMRoteirizado([TimeoutError("lento")])
    with pytest.raises(TimeoutError):
        await rodar_agente("oi", None, None, _pratos(), llm)


async def test_aceita_chave_explicacoes_com_acento():
    pratos = _pratos()
    llm = LLMRoteirizado(
        [
            _busca(),
            _escrita(principal_id="a", explicações={"a": "Do jeito que pediu."}),
        ]
    )
    r = await rodar_agente("algo", None, None, pratos, llm)
    assert r.explicacoes["a"] == "Do jeito que pediu."
