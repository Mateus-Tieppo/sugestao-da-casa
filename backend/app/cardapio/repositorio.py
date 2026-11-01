import asyncio
import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

from app.config import Settings, get_settings
from app.domain.modelos import Eixo, Prato, Restricao

CAMINHO_CARDAPIO = Path(__file__).resolve().parents[3] / "supabase" / "cardapio.json"
TTL_CACHE_S = 600.0

# Consulta única: prato com o restaurante embutido (PostgREST).
SELECT_PRATOS = "*, restaurantes(nome, taxa_entrega_centavos, tempo_entrega_min)"


class ConfiguracaoAusente(RuntimeError):
    """Faltam SUPABASE_URL e/ou SUPABASE_ANON_KEY."""


class Repositorio(Protocol):
    async def pratos(self) -> list[Prato]: ...


def linha_para_prato(linha: dict[str, Any]) -> Prato:
    """Converte uma linha de `pratos` (com `restaurantes` embutido) em Prato."""
    restaurante = linha["restaurantes"]
    eixos = {
        eixo: linha[eixo.value] for eixo in Eixo if linha.get(eixo.value) is not None
    }
    return Prato(
        id=linha["id"],
        nome=linha["nome"],
        descricao=linha["descricao"],
        restaurante_id=linha["restaurante_id"],
        restaurante_nome=restaurante["nome"],
        preco_centavos=linha["preco_centavos"],
        taxa_entrega_centavos=restaurante["taxa_entrega_centavos"],
        tempo_min=restaurante["tempo_entrega_min"] + linha["tempo_preparo_min"],
        ingredientes=list(linha["ingredientes"]),
        atende={Restricao(r) for r in linha["atende"]},
        eixos=eixos,
        foto_url=linha.get("foto_url"),
        doce=bool(linha.get("doce", False)),
    )


class RepositorioMemoria:
    def __init__(self, pratos: list[Prato]) -> None:
        self._pratos = pratos

    async def pratos(self) -> list[Prato]:
        return list(self._pratos)


class RepositorioArquivo:
    """Lê supabase/cardapio.json: desenvolvimento local sem banco."""

    def __init__(self, caminho: Path = CAMINHO_CARDAPIO) -> None:
        self._caminho = caminho

    async def pratos(self) -> list[Prato]:
        dados = json.loads(self._caminho.read_text(encoding="utf-8"))
        linhas = []
        for restaurante in dados["restaurantes"]:
            embutido = {
                k: restaurante[k]
                for k in ("nome", "taxa_entrega_centavos", "tempo_entrega_min")
            }
            for prato in restaurante["pratos"]:
                linhas.append(
                    {
                        **prato,
                        "restaurante_id": restaurante["id"],
                        "restaurantes": embutido,
                    }
                )
        return [linha_para_prato(linha) for linha in linhas]


class RepositorioSupabase:
    """Lê o cardápio do Supabase com a anon key e guarda em memória por 10 min."""

    def __init__(
        self,
        settings: Settings | None = None,
        cliente: Any = None,
        agora: Callable[[], float] = time.monotonic,
        ttl_s: float = TTL_CACHE_S,
    ) -> None:
        if cliente is None:
            cfg = settings or get_settings()
            if not cfg.supabase_url or not cfg.supabase_anon_key:
                raise ConfiguracaoAusente(
                    "Defina SUPABASE_URL e SUPABASE_ANON_KEY para usar o RepositorioSupabase"
                )
            from supabase import create_client

            cliente = create_client(cfg.supabase_url, cfg.supabase_anon_key)
        self._cliente = cliente
        self._agora = agora
        self._ttl_s = ttl_s
        self._cache: list[Prato] | None = None
        self._expira_em = 0.0

    def _consultar(self) -> list[Prato]:
        resposta = self._cliente.table("pratos").select(SELECT_PRATOS).execute()
        return [linha_para_prato(linha) for linha in resposta.data]

    async def pratos(self) -> list[Prato]:
        if self._cache is None or self._agora() >= self._expira_em:
            self._cache = await asyncio.to_thread(self._consultar)
            self._expira_em = self._agora() + self._ttl_s
        return list(self._cache)
