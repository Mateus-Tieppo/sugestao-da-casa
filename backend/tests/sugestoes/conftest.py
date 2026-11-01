import asyncio

import httpx
import openai
import pytest
from fastapi.testclient import TestClient

from app.cardapio.repositorio import RepositorioArquivo
from app.config import Settings
from app.main import app, obter_llm, obter_repositorio, obter_settings


def erro_429() -> openai.RateLimitError:
    req = httpx.Request("POST", "http://llm.local/v1/chat/completions")
    return openai.RateLimitError(
        "limite", response=httpx.Response(429, request=req), body=None
    )


class LLMQueFalha:
    async def conversar(self, mensagens, ferramentas=None, json=False):
        raise erro_429()


class LLMLento:
    async def conversar(self, mensagens, ferramentas=None, json=False):
        await asyncio.sleep(2)
        raise AssertionError("não deveria chegar aqui")


class RepositorioQuebrado:
    async def pratos(self):
        raise ConnectionError("banco fora do ar")


@pytest.fixture
def repo():
    return RepositorioArquivo()


@pytest.fixture
def cliente_http(repo):
    app.dependency_overrides[obter_repositorio] = lambda: repo
    app.dependency_overrides[obter_llm] = lambda: LLMQueFalha()
    app.dependency_overrides[obter_settings] = lambda: Settings(llm_timeout_s=1.0)
    yield TestClient(app)
    app.dependency_overrides.clear()
