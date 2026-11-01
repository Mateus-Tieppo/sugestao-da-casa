"""Contrato HTTP de POST /v1/sugestoes (o frontend espelha em lib/tipos.ts)."""

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.domain.modelos import Criterios


class PedidoSugestao(BaseModel):
    texto: str | None = Field(default=None, max_length=300)
    criterios: Criterios | None = None
    prato_atual_id: str | None = None

    @model_validator(mode="after")
    def _texto_ou_criterios(self) -> "PedidoSugestao":
        if not (self.texto or "").strip() and self.criterios is None:
            raise ValueError("informe um texto não vazio ou criterios")
        return self


class PratoSugerido(BaseModel):
    id: str
    nome: str
    restaurante: str
    preco_centavos: int
    taxa_entrega_centavos: int
    total_centavos: int
    tempo_min: int
    foto_url: str | None
    etiquetas: list[str]
    explicacao: str
    diferenca: str | None


class Etiqueta(BaseModel):
    chave: str
    rotulo: str


class MudancaSugerida(BaseModel):
    campo: Literal["orcamento", "tempo"]
    valor_atual: int
    valor_sugerido: int


class PropostaSugerida(BaseModel):
    mudancas: list[MudancaSugerida]  # 1 ou 2 itens, orçamento primeiro
    mensagem: str
    prato: PratoSugerido


class RespostaSugestao(BaseModel):
    status: Literal["ok", "sem_resultado"]
    modo: Literal["ia", "demonstracao"]
    criterios: Criterios
    entendido: list[Etiqueta]
    frase_decisao: str | None
    principal: PratoSugerido | None
    alternativas: list[PratoSugerido]
    proposta: PropostaSugerida | None
