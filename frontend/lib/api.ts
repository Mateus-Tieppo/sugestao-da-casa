import type { PedidoSugestao, RespostaSugestao } from "./tipos";

export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/+$/, "");
export const TIMEOUT_MS = 12_000;

export type TipoFalha = "timeout" | "rede" | "servidor";

export class FalhaApi extends Error {
  readonly tipo: TipoFalha;
  constructor(tipo: TipoFalha) {
    super(`falha na API: ${tipo}`);
    this.name = "FalhaApi";
    this.tipo = tipo;
  }
}

function erroDeCancelamento(): Error {
  return new DOMException("pedido cancelado", "AbortError");
}

export function ehCancelamento(e: unknown): boolean {
  return e instanceof Error && e.name === "AbortError";
}

/**
 * POST /v1/sugestoes. Rejeita com FalhaApi (timeout após 12 s, rede, servidor)
 * ou com AbortError quando `sinal` é cancelado pelo chamador.
 */
export function pedirSugestao(pedido: PedidoSugestao, sinal: AbortSignal): Promise<RespostaSugestao> {
  return new Promise<RespostaSugestao>((resolve, reject) => {
    if (sinal.aborted) {
      reject(erroDeCancelamento());
      return;
    }
    const interno = new AbortController();
    const limpar = () => {
      clearTimeout(temporizador);
      sinal.removeEventListener("abort", aoCancelar);
    };
    const aoCancelar = () => {
      limpar();
      interno.abort();
      reject(erroDeCancelamento());
    };
    // O prazo vale para a resposta inteira e não depende do fetch reagir ao abort.
    const temporizador = setTimeout(() => {
      limpar();
      interno.abort();
      reject(new FalhaApi("timeout"));
    }, TIMEOUT_MS);
    sinal.addEventListener("abort", aoCancelar, { once: true });

    fetch(`${API_URL}/v1/sugestoes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(pedido),
      signal: interno.signal,
    })
      .then(async (res) => {
        if (!res.ok) throw new FalhaApi("servidor");
        let dados: RespostaSugestao;
        try {
          dados = (await res.json()) as RespostaSugestao;
        } catch {
          throw new FalhaApi("servidor");
        }
        limpar();
        resolve(dados);
      })
      .catch((e: unknown) => {
        limpar();
        reject(e instanceof FalhaApi ? e : new FalhaApi("rede"));
      });
  });
}

/** Acorda o backend (cold start) sem esperar nem reportar falhas. */
export function aquecer(): void {
  fetch(`${API_URL}/health`).catch(() => {});
}
