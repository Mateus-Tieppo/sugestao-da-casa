"""Contrato HTTP de POST /v1/sugestoes (o frontend espelha em lib/tipos.ts)."""

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.domain.modelos import Criterios

MAX_INGREDIENTES = 20
MAX_TAMANHO_INGREDIENTE = 40
MAX_ORCAMENTO_CENTAVOS = 100_000
MAX_TEMPO_MIN = 240


class PedidoSugestao(BaseModel):
    texto: str | None = Field(default=None, max_length=300)
    criterios: Criterios | None = None
    prato_atual_id: str | None = Field(default=None, max_length=64)

    @model_validator(mode="after")
    def _criterios_dentro_dos_limites(self) -> "PedidoSugestao":
        c = self.criterios
        if c is None:
            return self
        if len(c.ingredientes_excluidos) > MAX_INGREDIENTES:
            raise ValueError(f"no máximo {MAX_INGREDIENTES} ingredientes excluídos")
        if any(len(i) > MAX_TAMANHO_INGREDIENTE for i in c.ingredientes_excluidos):
            raise ValueError(
                f"ingrediente com mais de {MAX_TAMANHO_INGREDIENTE} caracteres"
            )
        if any(not 0 <= v <= 100 for v in c.alvos.values()):
            raise ValueError("alvos devem ir de 0 a 100")
        o = c.orcamento_max_centavos
        if o is not None and not 0 <= o <= MAX_ORCAMENTO_CENTAVOS:
            raise ValueError("orçamento fora do limite")
        t = c.tempo_max_min
        if t is not None and not 1 <= t <= MAX_TEMPO_MIN:
            raise ValueError("tempo fora do limite")
        return self

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
