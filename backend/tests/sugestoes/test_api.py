import pytest

from app.main import app, obter_repositorio
from tests.sugestoes.conftest import RepositorioQuebrado


def test_post_sugestoes_sem_resultado(cliente_http):
    r = cliente_http.post(
        "/v1/sugestoes",
        json={"texto": "vegano, sem glúten, até R$ 15, em 10 min"},
    )
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["modo"] == "demonstracao"
    assert corpo["status"] == "sem_resultado"
    assert corpo["principal"] is None
    assert [m["campo"] for m in corpo["proposta"]["mudancas"]] == ["orcamento", "tempo"]
    assert corpo["proposta"]["mensagem"]
    assert corpo["proposta"]["prato"]["explicacao"]


def test_sem_resultado_com_um_campo_so(cliente_http):
    r = cliente_http.post(
        "/v1/sugestoes", json={"texto": "vegano, sem glúten, até R$ 15"}
    )
    corpo = r.json()
    assert corpo["status"] == "sem_resultado"
    assert [m["campo"] for m in corpo["proposta"]["mudancas"]] == ["orcamento"]


def test_post_sugestoes_ok_tem_o_contrato(cliente_http):
    r = cliente_http.post(
        "/v1/sugestoes", json={"texto": "algo quentinho, sem lactose"}
    )
    corpo = r.json()
    assert r.status_code == 200 and corpo["status"] == "ok"
    assert set(corpo) == {
        "status", "modo", "criterios", "entendido", "frase_decisao",
        "principal", "alternativas", "proposta",
    }  # fmt: skip
    assert set(corpo["principal"]) == {
        "id", "nome", "restaurante", "preco_centavos", "taxa_entrega_centavos",
        "total_centavos", "tempo_min", "foto_url", "etiquetas", "explicacao",
        "diferenca",
    }  # fmt: skip
    assert corpo["proposta"] is None


def test_texto_longo_da_422(cliente_http):
    assert (
        cliente_http.post("/v1/sugestoes", json={"texto": "a" * 301}).status_code == 422
    )


def test_pedido_vazio_da_422(cliente_http):
    assert cliente_http.post("/v1/sugestoes", json={}).status_code == 422
    assert cliente_http.post("/v1/sugestoes", json={"texto": "   "}).status_code == 422


def test_remover_etiqueta_sem_texto_via_http(cliente_http):
    r = cliente_http.post(
        "/v1/sugestoes", json={"criterios": {"restricoes": ["vegano"]}}
    )
    assert r.status_code == 200
    assert [e["chave"] for e in r.json()["entendido"]] == ["restricao:vegano"]


def test_repositorio_fora_do_ar_da_503(cliente_http):
    app.dependency_overrides[obter_repositorio] = lambda: RepositorioQuebrado()
    r = cliente_http.post("/v1/sugestoes", json={"texto": "algo leve"})
    assert r.status_code == 503
    assert r.json() == {"detalhe": "cardapio_indisponivel"}


@pytest.mark.parametrize(
    "criterios",
    [
        {"ingredientes_excluidos": [f"ing{i}" for i in range(21)]},
        {"ingredientes_excluidos": ["x" * 41]},
        {"alvos": {"peso": 101}},
        {"alvos": {"peso": -1}},
        {"orcamento_max_centavos": 100001},
        {"orcamento_max_centavos": -1},
        {"tempo_max_min": 0},
        {"tempo_max_min": 241},
    ],
)
def test_criterios_fora_dos_limites_dao_422(cliente_http, criterios):
    r = cliente_http.post("/v1/sugestoes", json={"criterios": criterios})
    assert r.status_code == 422


def test_prato_atual_id_longo_da_422(cliente_http):
    r = cliente_http.post(
        "/v1/sugestoes", json={"texto": "algo", "prato_atual_id": "x" * 65}
    )
    assert r.status_code == 422


def test_limites_nas_bordas_sao_aceitos(cliente_http):
    r = cliente_http.post(
        "/v1/sugestoes",
        json={
            "criterios": {
                "ingredientes_excluidos": [f"{i:02d}" + "x" * 38 for i in range(20)],
                "alvos": {"peso": 0, "conforto": 100},
                "orcamento_max_centavos": 100000,
                "tempo_max_min": 1,
            },
            "prato_atual_id": "x" * 64,
        },
    )
    assert r.status_code == 200


def test_falha_total_da_demonstracao_da_503_indisponivel(cliente_http, monkeypatch):
    def quebra(*a, **k):
        raise RuntimeError("bug")

    monkeypatch.setattr("app.sugestoes.servico._demonstracao", quebra)
    r = cliente_http.post("/v1/sugestoes", json={"texto": "algo leve"})
    assert r.status_code == 503
    assert r.json() == {"detalhe": "indisponivel"}
