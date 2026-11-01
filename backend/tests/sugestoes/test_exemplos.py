"""Os dois exemplos da tela inicial, em modo demonstração, com o cardápio real."""

import pytest

from app.cardapio.repositorio import RepositorioArquivo
from app.domain.filtro import passa_restricoes
from app.domain.modelos import Eixo
from app.sugestoes.esquemas import PedidoSugestao
from app.sugestoes.servico import sugerir
from tests.sugestoes.conftest import LLMQueFalha

EXEMPLOS = [
    "algo quentinho, não muito pesado, até R$ 40, sem lactose",
    "quero algo fresquinho e rápido, sem glúten",
]


@pytest.mark.parametrize("texto", EXEMPLOS)
async def test_exemplo_da_tela_inicial_nao_sugere_doce(texto):
    repo = RepositorioArquivo()
    pratos = {p.id: p for p in await repo.pratos()}
    r = await sugerir(PedidoSugestao(texto=texto), repo, LLMQueFalha(), timeout_s=5)
    assert r.modo == "demonstracao"
    assert r.status == "ok"
    assert r.principal is not None
    escolhidos = [r.principal, *r.alternativas]
    assert all(not pratos[p.id].doce for p in escolhidos)
    assert passa_restricoes(pratos[r.principal.id], r.criterios)


async def test_fresquinho_e_rapido_traz_prato_fresco():
    repo = RepositorioArquivo()
    pratos = {p.id: p for p in await repo.pratos()}
    r = await sugerir(
        PedidoSugestao(texto=EXEMPLOS[1]), repo, LLMQueFalha(), timeout_s=5
    )
    assert r.principal is not None
    assert pratos[r.principal.id].eixos[Eixo.temperatura] <= 40
