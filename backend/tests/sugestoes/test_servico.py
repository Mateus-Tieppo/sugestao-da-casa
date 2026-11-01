import time

import pytest

from app.demo.interpretador import rotulos
from app.domain.modelos import Criterios, Restricao
from app.llm.cliente import RespostaLLM
from app.sugestoes.esquemas import PedidoSugestao
from app.sugestoes.servico import CardapioIndisponivel, sugerir
from tests.agente.llm_falso import LLMRoteirizado
from tests.sugestoes.conftest import (
    LLMLento,
    LLMQueFalha,
    RepositorioQuebrado,
)


async def test_sugerir_cai_em_demonstracao_quando_llm_falha(repo):
    pedido = PedidoSugestao(texto="algo quentinho, até R$40, sem lactose")
    r = await sugerir(pedido, repo, LLMQueFalha(), timeout_s=5)
    assert r.modo == "demonstracao"
    assert r.status == "ok"
    assert r.principal is not None
    assert Restricao.sem_lactose in r.criterios.restricoes
    assert r.principal.total_centavos <= 4000
    assert "sem lactose" in r.principal.etiquetas


async def test_sugerir_respeita_timeout(repo):
    inicio = time.monotonic()
    r = await sugerir(
        PedidoSugestao(texto="algo leve"), repo, LLMLento(), timeout_s=0.1
    )
    assert time.monotonic() - inicio < 1
    assert r.modo == "demonstracao"


async def test_remover_etiqueta_sem_texto(repo):
    sem = Criterios(restricoes={Restricao.vegetariano})
    r = await sugerir(PedidoSugestao(criterios=sem), repo, LLMQueFalha(), 5)
    assert r.criterios == sem
    assert [e.chave for e in r.entendido] == ["restricao:vegetariano"]


async def test_prato_atual_desconhecido_vira_none(repo):
    r = await sugerir(
        PedidoSugestao(texto="mais barato", prato_atual_id="nao-existe"),
        repo,
        LLMQueFalha(),
        5,
    )
    assert r.status == "ok"
    assert r.criterios.orcamento_max_centavos is None


async def test_prato_atual_conhecido_aplica_ajuste(repo):
    atual = (await repo.pratos())[0]
    r = await sugerir(
        PedidoSugestao(texto="mais barato", prato_atual_id=atual.id),
        repo,
        LLMQueFalha(),
        5,
    )
    assert r.criterios.orcamento_max_centavos == max(0, atual.total_centavos - 100)


async def test_etiquetas_sao_restricoes_atendidas_mais_tempo(repo):
    pedido = PedidoSugestao(
        criterios=Criterios(restricoes={Restricao.vegetariano, Restricao.sem_lactose})
    )
    r = await sugerir(pedido, repo, LLMQueFalha(), 5)
    pratos = {p.id: p for p in await repo.pratos()}
    for sugerido in [r.principal, *r.alternativas]:
        original = pratos[sugerido.id]
        esperado = [
            rot
            for k, rot in rotulos(
                Criterios(restricoes=pedido.criterios.restricoes & original.atende)
            )
        ]
        assert sugerido.etiquetas == [*esperado, f"{original.tempo_min} min"]
        assert sugerido.etiquetas[-1].endswith(" min")


async def test_modo_ia_e_demonstracao_tem_o_mesmo_formato(repo):
    pedido = PedidoSugestao(
        criterios=Criterios(restricoes={Restricao.sem_lactose}, barato=True)
    )
    demo = await sugerir(pedido, repo, LLMQueFalha(), 5)
    llm = LLMRoteirizado([RespostaLLM(conteudo="{}")])
    ia = await sugerir(pedido, repo, llm, 5)
    assert ia.modo == "ia" and demo.modo == "demonstracao"
    a, b = ia.model_dump(), demo.model_dump()
    a.pop("modo"), b.pop("modo")
    assert a == b
    assert ia.principal.explicacao and ia.principal.etiquetas


async def test_repositorio_quebrado_levanta_cardapio_indisponivel():
    with pytest.raises(CardapioIndisponivel):
        await sugerir(
            PedidoSugestao(texto="algo"), RepositorioQuebrado(), LLMQueFalha(), 5
        )
