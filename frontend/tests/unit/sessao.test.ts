import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { estadoInicial, reducerSessao, useSessao } from "@/lib/sessao";
import type { PedidoSugestao, PropostaSugerida } from "@/lib/tipos";
import { criteriosBase, prato, respostaOk } from "./fixtures";

interface Pendente {
  corpo: PedidoSugestao;
  resolver: (r: Response) => void;
  sinal: AbortSignal | null | undefined;
}

function simularFetch() {
  const pendentes: Pendente[] = [];
  const mock = vi.fn((_url: string, init: RequestInit) => {
    return new Promise<Response>((resolve) => {
      pendentes.push({ corpo: JSON.parse(init.body as string), resolver: resolve, sinal: init.signal });
    });
  });
  vi.stubGlobal("fetch", mock);
  return pendentes;
}

const json = (o: unknown) => new Response(JSON.stringify(o), { status: 200 });

beforeEach(() => vi.useFakeTimers());
afterEach(() => vi.useRealTimers());

describe("useSessao", () => {
  it("entra em pensando de forma síncrona", () => {
    simularFetch();
    const { result } = renderHook(() => useSessao());
    expect(result.current.estado.fase).toBe("inicio");
    act(() => result.current.enviar("quero algo leve"));
    expect(result.current.estado.fase).toBe("pensando");
    expect(result.current.estado.ultimoPedido).toEqual({ texto: "quero algo leve", criterios: null, prato_atual_id: null });
  });

  it("mostra erro amigável quando a API não responde", async () => {
    vi.stubGlobal("fetch", vi.fn(() => new Promise(() => {})));
    const { result } = renderHook(() => useSessao());
    act(() => result.current.enviar("oi"));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(12_000);
    });
    expect(result.current.estado.fase).toBe("falha");
    expect(result.current.estado.erro).toBe("timeout");
  });

  it("ignora resposta antiga quando um pedido novo foi feito", async () => {
    const pendentes = simularFetch();
    const { result } = renderHook(() => useSessao());
    act(() => result.current.enviar("primeiro"));
    act(() => result.current.enviar("segundo"));
    expect(pendentes[0].sinal?.aborted).toBe(true);
    await act(async () => pendentes[1].resolver(json(respostaOk("segundo"))));
    await act(async () => pendentes[0].resolver(json(respostaOk("primeiro"))));
    expect(result.current.estado.fase).toBe("resultado");
    expect(result.current.estado.resposta?.principal?.id).toBe("segundo");
  });

  it("ignora falha antiga depois de um pedido novo", async () => {
    const pendentes = simularFetch();
    const { result } = renderHook(() => useSessao());
    act(() => result.current.enviar("primeiro"));
    act(() => result.current.enviar("segundo"));
    await act(async () => pendentes[0].resolver(new Response("{}", { status: 500 })));
    expect(result.current.estado.fase).toBe("pensando");
    await act(async () => pendentes[1].resolver(json(respostaOk("segundo"))));
    expect(result.current.estado.fase).toBe("resultado");
  });

  it("envia criterios e prato atual no refinamento", async () => {
    const pendentes = simularFetch();
    const { result } = renderHook(() => useSessao());
    act(() => result.current.enviar("algo"));
    await act(async () => pendentes[0].resolver(json(respostaOk("p1"))));
    act(() => result.current.enviar("mais barato"));
    expect(pendentes[1].corpo).toEqual({ texto: "mais barato", criterios: criteriosBase, prato_atual_id: "p1" });
  });

  it("remover etiqueta reenvia sem texto", async () => {
    const pendentes = simularFetch();
    const { result } = renderHook(() => useSessao());
    act(() => result.current.enviar("algo"));
    await act(async () => pendentes[0].resolver(json(respostaOk("p1"))));
    act(() => result.current.removerEtiqueta("orcamento"));
    expect(result.current.estado.fase).toBe("pensando");
    expect(pendentes[1].corpo.texto).toBeNull();
    expect(pendentes[1].corpo.criterios).toEqual({ ...criteriosBase, orcamento_max_centavos: null });
    expect(pendentes[1].corpo.prato_atual_id).toBe("p1");
  });

  it("aceitar proposta reenvia com todas as mudanças aplicadas, sem texto nem prato atual", async () => {
    const pendentes = simularFetch();
    const { result } = renderHook(() => useSessao());
    const proposta: PropostaSugerida = {
      mudancas: [
        { campo: "orcamento", valor_atual: 3000, valor_sugerido: 3600 },
        { campo: "tempo", valor_atual: 40, valor_sugerido: 55 },
      ],
      mensagem: "subir um pouco",
      prato: prato("novo"),
    };
    act(() => result.current.enviar("algo"));
    await act(async () =>
      pendentes[0].resolver(json({ ...respostaOk("x"), status: "sem_resultado", principal: null, proposta })),
    );
    expect(result.current.estado.fase).toBe("sem_resultado");
    act(() => result.current.aceitarProposta());
    expect(pendentes[1].corpo).toEqual({
      texto: null,
      criterios: { ...criteriosBase, orcamento_max_centavos: 3600, tempo_max_min: 55 },
      prato_atual_id: null,
    });
  });

  it("tentar de novo reenvia o último pedido", async () => {
    const pendentes = simularFetch();
    const { result } = renderHook(() => useSessao());
    act(() => result.current.enviar("algo"));
    await act(async () => pendentes[0].resolver(new Response("{}", { status: 500 })));
    expect(result.current.estado.fase).toBe("falha");
    expect(result.current.estado.erro).toBe("servidor");
    act(() => result.current.tentarDeNovo());
    expect(result.current.estado.fase).toBe("pensando");
    expect(pendentes[1].corpo).toEqual(pendentes[0].corpo);
  });

  it("cancela o pedido em andamento ao desmontar", () => {
    const pendentes = simularFetch();
    const { result, unmount } = renderHook(() => useSessao());
    act(() => result.current.enviar("algo"));
    unmount();
    expect(pendentes[0].sinal?.aborted).toBe(true);
  });
});

describe("reducerSessao", () => {
  it("vai de início a pensando a resultado e guarda a resposta", () => {
    const pedido = { texto: "x" };
    let e = reducerSessao(estadoInicial, { tipo: "enviado", pedido });
    expect(e.fase).toBe("pensando");
    const r = respostaOk("a");
    e = reducerSessao(e, { tipo: "respondido", resposta: r });
    expect(e).toMatchObject({ fase: "resultado", resposta: r, erro: null });
  });

  it("status sem_resultado vira fase sem_resultado", () => {
    const r = { ...respostaOk("a"), status: "sem_resultado" as const, principal: null };
    const e = reducerSessao(estadoInicial, { tipo: "respondido", resposta: r });
    expect(e.fase).toBe("sem_resultado");
  });

  it("falha mantém a última resposta para a tela poder mostrá-la", () => {
    const r = respostaOk("a");
    let e = reducerSessao(estadoInicial, { tipo: "respondido", resposta: r });
    e = reducerSessao(e, { tipo: "enviado", pedido: { texto: "y" } });
    e = reducerSessao(e, { tipo: "falhou", erro: "rede" });
    expect(e).toMatchObject({ fase: "falha", erro: "rede", resposta: r });
  });
});
