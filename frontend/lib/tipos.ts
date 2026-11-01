// Espelha backend/app/sugestoes/esquemas.py e backend/app/domain/modelos.py.
// Conjuntos (set) do Python viajam como arrays.

export type Restricao =
  | "sem_lactose"
  | "sem_gluten"
  | "vegetariano"
  | "vegano"
  | "sem_amendoim"
  | "sem_frutos_do_mar"
  | "sem_ovo";

export type Eixo = "temperatura" | "peso" | "picancia" | "conforto";

export interface Criterios {
  restricoes: Restricao[];
  /** minúsculas, sem acento */
  ingredientes_excluidos: string[];
  orcamento_max_centavos: number | null;
  tempo_max_min: number | null;
  /** 0 a 100 */
  alvos: Partial<Record<Eixo, number>>;
  barato: boolean;
  rapido: boolean;
}

export interface PedidoSugestao {
  /** até 300 caracteres */
  texto?: string | null;
  criterios?: Criterios | null;
  /** até 64 caracteres */
  prato_atual_id?: string | null;
}

export interface PratoSugerido {
  id: string;
  nome: string;
  restaurante: string;
  preco_centavos: number;
  taxa_entrega_centavos: number;
  total_centavos: number;
  tempo_min: number;
  foto_url: string | null;
  etiquetas: string[];
  explicacao: string;
  diferenca: string | null;
}

export interface Etiqueta {
  chave: string;
  rotulo: string;
}

export interface MudancaSugerida {
  campo: "orcamento" | "tempo";
  valor_atual: number;
  valor_sugerido: number;
}

export interface PropostaSugerida {
  /** 1 ou 2 itens, orçamento primeiro */
  mudancas: MudancaSugerida[];
  mensagem: string;
  prato: PratoSugerido;
}

export interface RespostaSugestao {
  status: "ok" | "sem_resultado";
  modo: "ia" | "demonstracao";
  criterios: Criterios;
  entendido: Etiqueta[];
  frase_decisao: string | null;
  principal: PratoSugerido | null;
  alternativas: PratoSugerido[];
  proposta: PropostaSugerida | null;
}

export const LIMITES = {
  texto: 300,
  ingredientes: 20,
  tamanhoIngrediente: 40,
  pratoAtualId: 64,
} as const;
