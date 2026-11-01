import pytest

from app.config import Settings


@pytest.fixture
def cliente_anon():
    """Cliente Supabase com a anon key; pula o teste se não houver banco acessível."""
    cfg = Settings()
    if not cfg.supabase_url or not cfg.supabase_anon_key:
        pytest.skip("SUPABASE_URL/SUPABASE_ANON_KEY não configurados")
    from supabase import create_client

    cliente = create_client(cfg.supabase_url, cfg.supabase_anon_key)
    try:
        cliente.table("pratos").select("id").limit(1).execute()
    except Exception as erro:  # noqa: BLE001 - qualquer falha de rede/schema vira skip
        pytest.skip(f"Supabase inacessível: {erro}")
    return cliente


@pytest.fixture
def repo_supabase(cliente_anon):
    from app.cardapio.repositorio import RepositorioSupabase

    return RepositorioSupabase(cliente=cliente_anon)
