import type { Page, Route } from "@playwright/test";
import { criteriosBase, prato, respostaOk } from "../unit/fixtures";
import type { Criterios, PedidoSugestao, PratoSugerido, RespostaSugestao } from "../../lib/tipos";

export const EXEMPLO = "algo quentinho, não muito pesado, até R$ 40, sem lactose";

export const CRITERIOS: Criterios = {
  ...criteriosBase,
  ingredientes_excluidos: [],
  orcamento_max_centavos: 4000,
  tempo_max_min: null,
  alvos: { temperatura: 80, peso: 30 },
};

export const CALDO: PratoSugerido = {
  ...prato("caldo"),
  nome: "Caldo verde",
  restaurante: "Cantina da Vó",
  preco_centavos: 2800,
  taxa_entrega_centavos: 400,
  total_centavos: 3200,
  tempo_min: 25,
  etiquetas: ["sem lactose", "25 min"],
  explicacao: "Quente e leve, feito com caldo de legumes e sem leite.",
};

export const LAMEN: PratoSugerido = {
  ...prato("lamen"),
  nome: "Lámen shoyu",
  restaurante: "Casa Tóquio",
  preco_centavos: 3200,
  taxa_entrega_centavos: 600,
  total_centavos: 3800,
  tempo_min: 30,
  etiquetas: ["sem lactose", "30 min"],
  explicacao: "Caldo quente de shoyu, sem lactose.",
  diferenca: "mais salgadinho",
};

export const CURRY: PratoSugerido = {
  ...prato("curry"),
  nome: "Curry de coco",
  restaurante: "Sabor da Índia",
  preco_centavos: 3000,
  taxa_entrega_centavos: 600,
  total_centavos: 3600,
  tempo_min: 35,
  etiquetas: ["sem lactose", "35 min"],
  explicacao: "Curry cremoso de leite de coco.",
  diferenca: "um toque de picância",
};

export const SOPA: PratoSugerido = {
  ...prato("sopa"),
  nome: "Sopa de abóbora",
  restaurante: "Cantina da Vó",
  preco_centavos: 1800,
  taxa_entrega_centavos: 400,
  total_centavos: 2200,
  tempo_min: 20,
  etiquetas: ["sem lactose", "20 min"],
  explicacao: "Mais em conta e igualmente quentinha.",
};

export const PRIMEIRA: RespostaSugestao = {
  ...respostaOk("caldo", CRITERIOS),
  modo: "ia",
  entendido: [
    { chave: "restricao:sem_lactose", rotulo: "sem lactose" },
    { chave: "orcamento", rotulo: "até R$\u00a040" },
    { chave: "alvo:temperatura", rotulo: "quentinho" },
    { chave: "alvo:peso", rotulo: "leve" },
  ],
  frase_decisao: "Hoje pede um Caldo verde.",
  principal: CALDO,
  alternativas: [LAMEN, CURRY],
};

/** Sem o "sem lactose": o pedido de remover a etiqueta chega com os critérios já sem ela. */
export const SEM_ETIQUETA: RespostaSugestao = {
  ...PRIMEIRA,
  criterios: { ...CRITERIOS, restricoes: [] },
  entendido: PRIMEIRA.entendido.filter((e) => e.chave !== "restricao:sem_lactose"),
  principal: { ...CALDO, etiquetas: ["25 min"] },
};

export const MAIS_BARATO: RespostaSugestao = {
  ...SEM_ETIQUETA,
  criterios: { ...SEM_ETIQUETA.criterios, barato: true },
  entendido: [...SEM_ETIQUETA.entendido, { chave: "barato", rotulo: "mais barato" }],
  frase_decisao: "Hoje pede uma Sopa de abóbora.",
  principal: { ...SOPA, etiquetas: ["20 min"], diferenca: null },
  alternativas: [CALDO, LAMEN],
};

export const CRITERIOS_APERTADOS: Criterios = {
  ...CRITERIOS,
  orcamento_max_centavos: 2000,
  tempo_max_min: 20,
};

export const PRATO_DA_PROPOSTA: PratoSugerido = {
  ...prato("risoto"),
  nome: "Risoto de cogumelos",
  restaurante: "Cantina da Vó",
  preco_centavos: 2000,
  taxa_entrega_centavos: 400,
  total_centavos: 2400,
  tempo_min: 28,
  etiquetas: ["sem lactose", "28 min"],
  explicacao: "Cremoso sem leite, pronto em 28 minutos.",
};

export const SEM_RESULTADO: RespostaSugestao = {
  status: "sem_resultado",
  modo: "ia",
  criterios: CRITERIOS_APERTADOS,
  entendido: [
    { chave: "restricao:sem_lactose", rotulo: "sem lactose" },
    { chave: "orcamento", rotulo: "até R$\u00a020" },
    { chave: "tempo", rotulo: "até 20 min" },
  ],
  frase_decisao: null,
  principal: null,
  alternativas: [],
  proposta: {
    mudancas: [
      { campo: "orcamento", valor_atual: 2000, valor_sugerido: 2400 },
      { campo: "tempo", valor_atual: 20, valor_sugerido: 30 },
    ],
    mensagem: "Com R$\u00a024 e 30 min, o Risoto de cogumelos serve.",
    prato: PRATO_DA_PROPOSTA,
  },
};

export const DEPOIS_DA_PROPOSTA: RespostaSugestao = {
  ...respostaOk("risoto", { ...CRITERIOS_APERTADOS, orcamento_max_centavos: 2400, tempo_max_min: 30 }),
  modo: "ia",
  entendido: [
    { chave: "restricao:sem_lactose", rotulo: "sem lactose" },
    { chave: "orcamento", rotulo: "até R$\u00a024" },
    { chave: "tempo", rotulo: "até 30 min" },
  ],
  frase_decisao: "Hoje pede um Risoto de cogumelos.",
  principal: PRATO_DA_PROPOSTA,
  alternativas: [],
};

export const COMO_DEMONSTRACAO = (r: RespostaSugestao): RespostaSugestao => ({ ...r, modo: "demonstracao" });

type Responder = (pedido: PedidoSugestao, n: number) => RespostaSugestao;

export interface Interceptacao {
  pedidos: PedidoSugestao[];
}

/**
 * Intercepta POST /v1/sugestoes (e o aquecimento em /health) com respostas fixas.
 * `atrasoMs` deixa o "pensando" visível antes da resposta chegar.
 */
export async function interceptarApi(page: Page, responder: Responder, atrasoMs = 500): Promise<Interceptacao> {
  const registro: Interceptacao = { pedidos: [] };
  const cors = { "access-control-allow-origin": "*", "access-control-allow-headers": "*" };

  await page.route("**/health", (route: Route) => route.fulfill({ status: 200, headers: cors, json: { status: "ok" } }));
  await page.route("**/v1/sugestoes", async (route: Route) => {
    if (route.request().method() === "OPTIONS") {
      await route.fulfill({ status: 204, headers: cors });
      return;
    }
    const pedido = route.request().postDataJSON() as PedidoSugestao;
    registro.pedidos.push(pedido);
    await new Promise((r) => setTimeout(r, atrasoMs));
    await route.fulfill({ status: 200, headers: cors, json: responder(pedido, registro.pedidos.length) });
  });
  return registro;
}
