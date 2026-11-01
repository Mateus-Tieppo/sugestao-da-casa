import type { Criterios, PratoSugerido, RespostaSugestao } from "@/lib/tipos";

export const criteriosBase: Criterios = {
  restricoes: ["sem_lactose"],
  ingredientes_excluidos: ["cebola"],
  orcamento_max_centavos: 3000,
  tempo_max_min: 40,
  alvos: { picancia: 80 },
  barato: false,
  rapido: false,
};

export function prato(id: string): PratoSugerido {
  return {
    id,
    nome: `Prato ${id}`,
    restaurante: "Casa",
    preco_centavos: 2500,
    taxa_entrega_centavos: 500,
    total_centavos: 3000,
    tempo_min: 30,
    foto_url: null,
    etiquetas: [],
    explicacao: "porque sim",
    diferenca: null,
  };
}

export function respostaOk(id: string, criterios: Criterios = criteriosBase): RespostaSugestao {
  return {
    status: "ok",
    modo: "demonstracao",
    criterios,
    entendido: [
      { chave: "orcamento", rotulo: "até R$ 30" },
      { chave: "tempo", rotulo: "até 40 min" },
    ],
    frase_decisao: "esse",
    principal: prato(id),
    alternativas: [],
    proposta: null,
  };
}
