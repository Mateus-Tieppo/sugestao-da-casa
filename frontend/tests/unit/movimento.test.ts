import { afterEach, describe, expect, it, vi } from "vitest";
import { COM_MOVIMENTO, comMovimento, SEM_MOVIMENTO } from "@/lib/movimento";

function simularPreferencia(reduzir: boolean) {
  const consultas: string[] = [];
  vi.stubGlobal(
    "matchMedia",
    vi.fn((query: string) => {
      consultas.push(query);
      return {
        matches: reduzir ? query === SEM_MOVIMENTO : query === COM_MOVIMENTO,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      };
    }),
  );
  return consultas;
}

describe("comMovimento", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("com reduced motion, roda só o ramo sem movimento", () => {
    const consultas = simularPreferencia(true);
    const animar = vi.fn();
    const semMovimento = vi.fn();

    const mm = comMovimento(document.body, animar, semMovimento);

    expect(semMovimento).toHaveBeenCalledTimes(1);
    expect(animar).not.toHaveBeenCalled();
    expect(consultas).toEqual(expect.arrayContaining([COM_MOVIMENTO, SEM_MOVIMENTO]));
    mm?.revert();
  });

  it("sem preferência, roda só a animação", () => {
    simularPreferencia(false);
    const animar = vi.fn();
    const semMovimento = vi.fn();

    const mm = comMovimento(document.body, animar, semMovimento);

    expect(animar).toHaveBeenCalledTimes(1);
    expect(semMovimento).not.toHaveBeenCalled();
    mm?.revert();
  });

  it("sem matchMedia no ambiente, não anima e não quebra", () => {
    vi.stubGlobal("matchMedia", undefined);
    const animar = vi.fn();
    const semMovimento = vi.fn();

    expect(comMovimento(document.body, animar, semMovimento)).toBeNull();
    expect(animar).not.toHaveBeenCalled();
    expect(semMovimento).not.toHaveBeenCalled();
  });
});
