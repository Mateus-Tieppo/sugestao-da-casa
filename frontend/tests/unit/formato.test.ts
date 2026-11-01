import { describe, expect, it } from "vitest";
import { formatarReais } from "@/lib/formato";

describe("formatarReais", () => {
  it("omite os centavos quando o valor é inteiro", () => {
    expect(formatarReais(3200)).toBe("R$ 32");
    expect(formatarReais(0)).toBe("R$ 0");
  });
  it("usa vírgula e duas casas quando há centavos", () => {
    expect(formatarReais(2250)).toBe("R$ 22,50");
    expect(formatarReais(2205)).toBe("R$ 22,05");
    expect(formatarReais(99)).toBe("R$ 0,99");
  });
});
