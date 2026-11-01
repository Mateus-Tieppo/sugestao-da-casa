from functools import lru_cache
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.cardapio.repositorio import (
    Repositorio,
    RepositorioArquivo,
    RepositorioSupabase,
)
from app.config import Settings, get_settings
from app.llm.cliente import ClienteLLM, ClienteOpenAICompativel
from app.sugestoes.esquemas import PedidoSugestao, RespostaSugestao
from app.sugestoes.servico import CardapioIndisponivel, sugerir

app = FastAPI(title="Sugestão da Casa")

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origens,
    allow_methods=["*"],
    allow_headers=["*"],
)


def obter_settings() -> Settings:
    return get_settings()


@lru_cache
def _repositorio_unico() -> Repositorio:
    s = get_settings()
    if s.supabase_url and s.supabase_anon_key:
        return RepositorioSupabase(s)
    return RepositorioArquivo()  # desenvolvimento local sem banco


def obter_repositorio() -> Repositorio:
    return _repositorio_unico()


def obter_llm(settings: Annotated[Settings, Depends(obter_settings)]) -> ClienteLLM:
    return ClienteOpenAICompativel(settings)


@app.exception_handler(CardapioIndisponivel)
async def _cardapio_indisponivel(request: Request, exc: CardapioIndisponivel):
    return JSONResponse(status_code=503, content={"detalhe": "cardapio_indisponivel"})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/sugestoes", response_model=RespostaSugestao)
async def post_sugestoes(
    pedido: PedidoSugestao,
    repo: Annotated[Repositorio, Depends(obter_repositorio)],
    llm: Annotated[ClienteLLM, Depends(obter_llm)],
    settings: Annotated[Settings, Depends(obter_settings)],
) -> RespostaSugestao:
    return await sugerir(pedido, repo, llm, settings.llm_timeout_s)
