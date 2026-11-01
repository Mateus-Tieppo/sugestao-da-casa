"""Testes de integração: exigem um Supabase com o seed aplicado."""

import pytest
from postgrest.exceptions import APIError

from app.domain.modelos import Restricao

pytestmark = pytest.mark.integracao


async def test_cada_restricao_tem_ao_menos_8_pratos(repo_supabase):
    pratos = await repo_supabase.pratos()
    assert len(pratos) >= 70
    for r in Restricao:
        assert sum(r in p.atende for p in pratos) >= 8, r


async def test_anon_nao_consegue_escrever(cliente_anon):
    with pytest.raises(APIError):
        cliente_anon.table("pratos").insert({"nome": "x"}).execute()
