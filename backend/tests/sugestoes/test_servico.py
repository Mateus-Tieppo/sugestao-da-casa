import time

import pytest

from app.demo.interpretador import rotulos
from app.domain.modelos import Criterios, Restricao
from app.llm.cliente import ChamadaFerramenta, RespostaLLM
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


async def test_log_do_fallback_nao_vaza_o_texto_do_usuario(repo, caplog):
    class LLMVazador:
        async def conversar(self, mensagens, ferramentas=None, json=False):
            raise ValueError("input inválido: segredo do usuario xyzzy")

    with caplog.at_level("DEBUG", logger="sugestoes"):
        await sugerir(PedidoSugestao(texto="xyzzy quentinho"), repo, LLMVazador(), 5)
    assert "ValueError" in caplog.text
    assert "xyzzy" not in caplog.text


async def test_log_do_repositorio_nao_vaza_mensagem(caplog):
    class RepoVazador:
        async def pratos(self):
            raise ConnectionError("senha=hunter2")

    with (
        caplog.at_level("DEBUG", logger="sugestoes"),
        pytest.raises(CardapioIndisponivel),
    ):
        await sugerir(PedidoSugestao(texto="algo"), RepoVazador(), LLMQueFalha(), 5)
    assert "ConnectionError" in caplog.text
    assert "hunter2" not in caplog.text


async def test_erro_nao_openai_do_agente_cai_em_demonstracao(repo, monkeypatch):
    async def quebra(*a, **k):
        raise ValueError("bug no agente")

    monkeypatch.setattr("app.sugestoes.servico.rodar_agente", quebra)
    r = await sugerir(PedidoSugestao(texto="algo leve"), repo, LLMQueFalha(), 5)
    assert r.modo == "demonstracao" and r.status == "ok"


async def test_algo_sem_carne_so_devolve_vegetarianos(repo):
    r = await sugerir(PedidoSugestao(texto="algo sem carne"), repo, LLMQueFalha(), 5)
    assert r.status == "ok"
    assert Restricao.vegetariano in r.criterios.restricoes
    por_id = {p.id: p for p in await repo.pratos()}
    devolvidos = [r.principal, *r.alternativas]
    assert devolvidos
    for d in devolvidos:
        assert Restricao.vegetariano in por_id[d.id].atende, d.nome


class LLMEscritaLenta:
    """Passo 1 responde na hora; o passo 2 (escrita) demora demais."""

    def __init__(self):
        self.chamadas = 0

    async def conversar(self, mensagens, ferramentas=None, json=False):
        import asyncio

        self.chamadas += 1
        if self.chamadas == 1:
            return RespostaLLM(
                chamadas=[
                    ChamadaFerramenta(nome="buscar_pratos", argumentos="{}")
                ]
            )
        await asyncio.sleep(5)
        return RespostaLLM(conteudo="{}")


async def test_escrita_lenta_mantem_modo_ia_com_textos_prontos(repo):
    inicio = time.monotonic()
    r = await sugerir(
        PedidoSugestao(texto="algo quentinho"), repo, LLMEscritaLenta(), timeout_s=2.0
    )
    assert time.monotonic() - inicio < 2.0
    assert r.modo == "ia"
    assert r.status == "ok"
    assert r.principal.explicacao
    assert r.frase_decisao and r.principal.nome in r.frase_decisao
