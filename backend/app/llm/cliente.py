"""Cliente LLM mínimo: um protocolo e a implementação para APIs compatíveis com OpenAI."""

from typing import Any, Protocol

from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from app.config import Settings, get_settings


class ChamadaFerramenta(BaseModel):
    nome: str
    argumentos: str
    id: str = "call_0"


class RespostaLLM(BaseModel):
    conteudo: str | None = None
    chamadas: list[ChamadaFerramenta] = Field(default_factory=list)


class ClienteLLM(Protocol):
    async def conversar(
        self,
        mensagens: list[dict],
        ferramentas: list[dict] | None = None,
        json: bool = False,
    ) -> RespostaLLM: ...


class ClienteOpenAICompativel:
    """Funciona com Ollama, vLLM, LM Studio e qualquer servidor com a API de chat da OpenAI."""

    def __init__(self, settings: Settings | None = None) -> None:
        s = settings or get_settings()
        self._modelo = s.llm_model
        self._cliente = AsyncOpenAI(
            base_url=s.llm_base_url, api_key=s.llm_api_key, timeout=s.llm_timeout_s
        )

    async def conversar(
        self,
        mensagens: list[dict],
        ferramentas: list[dict] | None = None,
        json: bool = False,
    ) -> RespostaLLM:
        opcoes: dict[str, Any] = {}
        if ferramentas:
            opcoes["tools"] = ferramentas
            opcoes["tool_choice"] = "auto"
        if json:
            opcoes["response_format"] = {"type": "json_object"}
        resposta = await self._cliente.chat.completions.create(
            model=self._modelo, messages=mensagens, temperature=0.2, **opcoes
        )
        msg = resposta.choices[0].message
        chamadas = [
            ChamadaFerramenta(
                nome=c.function.name, argumentos=c.function.arguments, id=c.id
            )
            for c in (msg.tool_calls or [])
            if c.type == "function"
        ]
        return RespostaLLM(conteudo=msg.content, chamadas=chamadas)
