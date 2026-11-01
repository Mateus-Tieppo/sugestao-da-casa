import type { PratoSugerido } from "./tipos";

export const QUANTIDADE_MINIMA = 1;
export const QUANTIDADE_MAXIMA = 10;

export interface ItemCarrinho {
  prato: PratoSugerido;
  quantidade: number;
}

export interface EstadoCarrinho {
  itens: ItemCarrinho[];
}

export type AcaoCarrinho =
  | { tipo: "adicionar"; prato: PratoSugerido }
  | { tipo: "alterarQuantidade"; id: string; quantidade: number }
  | { tipo: "limpar" };

function limitar(n: number): number {
  return Math.min(QUANTIDADE_MAXIMA, Math.max(QUANTIDADE_MINIMA, Math.round(n) || QUANTIDADE_MINIMA));
}

export function reduzirCarrinho(estado: EstadoCarrinho, acao: AcaoCarrinho): EstadoCarrinho {
  switch (acao.tipo) {
    case "adicionar": {
      const existe = estado.itens.some((i) => i.prato.id === acao.prato.id);
      return {
        itens: existe
          ? estado.itens.map((i) =>
              i.prato.id === acao.prato.id ? { ...i, quantidade: limitar(i.quantidade + 1) } : i,
            )
          : [...estado.itens, { prato: acao.prato, quantidade: 1 }],
      };
    }
    case "alterarQuantidade":
      return {
        itens: estado.itens.map((i) => (i.prato.id === acao.id ? { ...i, quantidade: limitar(acao.quantidade) } : i)),
      };
    case "limpar":
      return { itens: [] };
  }
}

/** Soma de preço vezes quantidade, mais a taxa de entrega de cada restaurante, uma vez só. */
export function subtotalCarrinho(estado: EstadoCarrinho): number {
  return estado.itens.reduce((soma, i) => soma + i.prato.preco_centavos * i.quantidade, 0);
}

/** Taxa de cada restaurante distinto do carrinho (a do primeiro prato dele). */
export function entregaCarrinho(estado: EstadoCarrinho): number {
  const taxas = new Map<string, number>();
  for (const i of estado.itens) if (!taxas.has(i.prato.restaurante)) taxas.set(i.prato.restaurante, i.prato.taxa_entrega_centavos);
  let soma = 0;
  for (const t of taxas.values()) soma += t;
  return soma;
}

export function totalCarrinho(estado: EstadoCarrinho): number {
  return subtotalCarrinho(estado) + entregaCarrinho(estado);
}

/** O pedido chega quando chega o prato mais demorado. */
export function tempoEstimadoMin(estado: EstadoCarrinho): number {
  return estado.itens.reduce((maior, i) => Math.max(maior, i.prato.tempo_min), 0);
}
