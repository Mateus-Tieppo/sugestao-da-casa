from app.main import app, obter_repositorio
from tests.sugestoes.conftest import RepositorioQuebrado


def test_post_sugestoes_sem_resultado(cliente_http):
    r = cliente_http.post(
        "/v1/sugestoes",
        json={"texto": "vegano, sem glúten, até R$ 15"},
    )
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["modo"] == "demonstracao"
    assert corpo["status"] == "sem_resultado"
    assert corpo["principal"] is None
    assert corpo["proposta"]["campo"] in {"orcamento", "tempo"}
    assert corpo["proposta"]["mensagem"]
    assert corpo["proposta"]["prato"]["explicacao"]


def test_sem_resultado_com_dois_limites_impossiveis_nao_quebra(cliente_http):
    # orçamento e tempo falham juntos: afrouxar um só não resolve, então não há proposta
    r = cliente_http.post(
        "/v1/sugestoes",
        json={"texto": "vegano, sem glúten, até R$ 15, em 10 min"},
    )
    corpo = r.json()
    assert r.status_code == 200
    assert corpo["status"] == "sem_resultado" and corpo["principal"] is None
    assert corpo["proposta"] is None


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
