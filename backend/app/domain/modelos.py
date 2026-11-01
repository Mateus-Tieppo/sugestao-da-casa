from enum import StrEnum

from pydantic import BaseModel, Field


class Restricao(StrEnum):
    sem_lactose = "sem_lactose"
    sem_gluten = "sem_gluten"
    vegetariano = "vegetariano"
    vegano = "vegano"
    sem_amendoim = "sem_amendoim"
    sem_frutos_do_mar = "sem_frutos_do_mar"
    sem_ovo = "sem_ovo"


class Eixo(StrEnum):
    """Eixos de 0 a 100. temperatura: 0 fresco, 100 quentinho. peso: 0 leve, 100 pesado."""

    temperatura = "temperatura"
    peso = "peso"
    picancia = "picancia"
    conforto = "conforto"


class Criterios(BaseModel):
    restricoes: set[Restricao] = Field(default_factory=set)
    # minúsculas, sem acento
    ingredientes_excluidos: set[str] = Field(default_factory=set)
    orcamento_max_centavos: int | None = None
    tempo_max_min: int | None = None
    alvos: dict[Eixo, int] = Field(default_factory=dict)  # 0 a 100
    barato: bool = False
    rapido: bool = False
    quer_doce: bool = False


class Prato(BaseModel):
    id: str
    nome: str
    descricao: str
    restaurante_id: str
    restaurante_nome: str
    preco_centavos: int
    taxa_entrega_centavos: int
    tempo_min: int
    ingredientes: list[str]
    atende: set[Restricao]
    eixos: dict[Eixo, int]
    foto_url: str | None
    doce: bool = False

    @property
    def total_centavos(self) -> int:
        return self.preco_centavos + self.taxa_entrega_centavos
