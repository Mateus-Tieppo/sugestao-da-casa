import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { aquecer, FalhaApi, lerTimeout, pedirSugestao, TIMEOUT_MS } from "@/lib/api";
import { respostaOk } from "./fixtures";

beforeEach(() => vi.useFakeTimers());
afterEach(() => vi.useRealTimers());

describe("pedirSugestao", () => {
  it("mostra erro amigável quando a API não responde (timeout de 12 s)", async () => {
    vi.stubGlobal("fetch", vi.fn(() => new Promise(() => {})));
    const p = pedirSugestao({ texto: "algo leve" }, new AbortController().signal);
    const visto = p.catch((e: unknown) => e);
    await vi.advanceTimersByTimeAsync(11_999);
    let resolvido = false;
    void visto.then(() => (resolvido = true));
    await Promise.resolve();
    expect(resolvido).toBe(false);
    await vi.advanceTimersByTimeAsync(1);
    const erro = await visto;
    expect(erro).toBeInstanceOf(FalhaApi);
    expect((erro as FalhaApi).tipo).toBe("timeout");
  });

  it("devolve a resposta e faz POST /v1/sugestoes com JSON", async () => {
    const fetchMock = vi.fn(async () => new Response(JSON.stringify(respostaOk("a")), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    const r = await pedirSugestao({ texto: "oi" }, new AbortController().signal);
    expect(r.principal?.id).toBe("a");
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("http://localhost:8000/v1/sugestoes");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body as string)).toEqual({ texto: "oi" });
  });

  it("classifica erro de rede e erro do servidor", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => { throw new TypeError("Failed to fetch"); }));
    await expect(pedirSugestao({ texto: "x" }, new AbortController().signal)).rejects.toMatchObject({ tipo: "rede" });
    vi.stubGlobal("fetch", vi.fn(async () => new Response("{}", { status: 500 })));
    await expect(pedirSugestao({ texto: "x" }, new AbortController().signal)).rejects.toMatchObject({ tipo: "servidor" });
    vi.stubGlobal("fetch", vi.fn(async () => new Response("<html>", { status: 200 })));
    await expect(pedirSugestao({ texto: "x" }, new AbortController().signal)).rejects.toMatchObject({ tipo: "servidor" });
  });

  it("propaga o cancelamento do chamador como AbortError, não como FalhaApi", async () => {
    vi.stubGlobal("fetch", vi.fn(() => new Promise(() => {})));
    const ctl = new AbortController();
    const p = pedirSugestao({ texto: "x" }, ctl.signal);
    const visto = p.catch((e: unknown) => e);
    ctl.abort();
    const erro = await visto;
    expect(erro).not.toBeInstanceOf(FalhaApi);
    expect((erro as Error).name).toBe("AbortError");
  });
});

describe("aquecer", () => {
  it("dispara GET /health sem esperar e engole falhas", async () => {
    const fetchMock = vi.fn(async () => { throw new TypeError("offline"); });
    vi.stubGlobal("fetch", fetchMock);
    expect(aquecer()).toBeUndefined();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect((fetchMock.mock.calls[0] as unknown[])[0]).toBe("http://localhost:8000/health");
    await vi.advanceTimersByTimeAsync(0);
  });
});

describe("timeout configurável", () => {
  it("o padrão é 12 s e valores inválidos voltam ao padrão", () => {
    expect(TIMEOUT_MS).toBe(12_000);
    expect(lerTimeout(undefined)).toBe(12_000);
    expect(lerTimeout("")).toBe(12_000);
    expect(lerTimeout("abc")).toBe(12_000);
    expect(lerTimeout("-5")).toBe(12_000);
    expect(lerTimeout("0")).toBe(12_000);
    expect(lerTimeout("60000")).toBe(60_000);
  });
});
