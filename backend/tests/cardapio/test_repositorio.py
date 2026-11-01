import pytest

from app.cardapio.repositorio import (
    CAMINHO_CARDAPIO,
    ConfiguracaoAusente,
    RepositorioArquivo,
    RepositorioMemoria,
    RepositorioSupabase,
)
from app.config import Settings
from app.domain.modelos import Eixo, Restricao
from tests.fabricas import prato

LINHA = {
    "id": "p1",
    "restaurante_id": "r1",
    "nome": "Caldo verde",
    "descricao": "Quentinho",
    "preco_centavos": 3200,
    "tempo_preparo_min": 5,
    "ingredientes": ["couve", "batata"],
    "atende": ["sem_lactose", "sem_ovo"],
    "temperatura": 90,
    "peso": 25,
    "picancia": None,
    "conforto": 80,
    "foto_url": None,
    "restaurantes": {
        "nome": "Vó Lina",
        "taxa_entrega_centavos": 600,
        "tempo_entrega_min": 25,
    },
}


class RespostaFalsa:
    def __init__(self, data):
        self.data = data


class ClienteFalso:
    """Imita client.table(...).select(...).execute() e conta as consultas."""

    def __init__(self, linhas):
        self.linhas = linhas
        self.consultas = 0
        self.tabelas = []
        self.selects = []

    def table(self, nome):
        self.tabelas.append(nome)
        return self

    def select(self, colunas):
        self.selects.append(colunas)
        return self

    def execute(self):
        self.consultas += 1
        return RespostaFalsa(self.linhas)


class Relogio:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


async def test_memoria_devolve_os_pratos():
    p = prato()
    assert await RepositorioMemoria([p]).pratos() == [p]


async def test_supabase_mapeia_linha_para_prato():
    cliente = ClienteFalso([LINHA])
    [p] = await RepositorioSupabase(cliente=cliente).pratos()
    assert cliente.tabelas == ["pratos"]
    assert "restaurantes" in cliente.selects[0]
    assert p.restaurante_nome == "Vó Lina"
    assert p.tempo_min == 30
    assert p.taxa_entrega_centavos == 600
    assert p.total_centavos == 3800
    assert p.atende == {Restricao.sem_lactose, Restricao.sem_ovo}
    assert p.eixos == {Eixo.temperatura: 90, Eixo.peso: 25, Eixo.conforto: 80}


async def test_cache_nao_consulta_de_novo_em_10_minutos():
    cliente, relogio = ClienteFalso([LINHA]), Relogio()
    repo = RepositorioSupabase(cliente=cliente, agora=relogio)
    await repo.pratos()
    relogio.t += 599
    await repo.pratos()
    assert cliente.consultas == 1


async def test_cache_expira_depois_de_10_minutos():
    cliente, relogio = ClienteFalso([LINHA]), Relogio()
    repo = RepositorioSupabase(cliente=cliente, agora=relogio)
    await repo.pratos()
    relogio.t += 601
    await repo.pratos()
    assert cliente.consultas == 2


def test_supabase_sem_configuracao_falha_com_erro_claro():
    cfg = Settings(_env_file=None, supabase_url="", supabase_anon_key="")
    with pytest.raises(ConfiguracaoAusente, match="SUPABASE_URL"):
        RepositorioSupabase(settings=cfg)


async def test_arquivo_carrega_ao_menos_70_pratos():
    pratos = await RepositorioArquivo().pratos()
    assert CAMINHO_CARDAPIO.exists()
    assert len(pratos) >= 70
    assert len({p.id for p in pratos}) == len(pratos)
