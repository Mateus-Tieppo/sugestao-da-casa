import { describe, expect, it } from "vitest";
import { reduzirCarrinho, totalCarrinho, type EstadoCarrinho } from "@/lib/carrinho";
import { prato } from "./fixtures";

const vazio: EstadoCarrinho = { itens: [] };

describe("carrinho", () => {
  it("carrinho soma taxa uma vez por restaurante", () => {
    const a = { ...prato("a"), restaurante: "Casa", preco_centavos: 2000, taxa_entrega_centavos: 500 };
    const b = { ...prato("b"), restaurante: "Casa", preco_centavos: 1000, taxa_entrega_centavos: 500 };
    const c = { ...prato("c"), restaurante: "Outra", preco_centavos: 3000, taxa_entrega_centavos: 700 };
    let e = reduzirCarrinho(vazio, { tipo: "adicionar", prato: a });
    e = reduzirCarrinho(e, { tipo: "adicionar", prato: b });
    expect(totalCarrinho(e)).toBe(2000 + 1000 + 500);
    e = reduzirCarrinho(e, { tipo: "alterarQuantidade", id: "a", quantidade: 2 });
    expect(totalCarrinho(e)).toBe(4000 + 1000 + 500);
    e = reduzirCarrinho(e, { tipo: "adicionar", prato: c });
    expect(totalCarrinho(e)).toBe(4000 + 1000 + 3000 + 500 + 700);
    expect(totalCarrinho(vazio)).toBe(0);
  });

  it("quantidade fica entre 1 e 10", () => {
    let e = reduzirCarrinho(vazio, { tipo: "adicionar", prato: prato("a") });
    e = reduzirCarrinho(e, { tipo: "alterarQuantidade", id: "a", quantidade: 0 });
    expect(e.itens[0].quantidade).toBe(1);
    e = reduzirCarrinho(e, { tipo: "alterarQuantidade", id: "a", quantidade: 99 });
    expect(e.itens[0].quantidade).toBe(10);
    e = reduzirCarrinho(e, { tipo: "alterarQuantidade", id: "a", quantidade: 4 });
    expect(e.itens[0].quantidade).toBe(4);
    e = reduzirCarrinho(e, { tipo: "alterarQuantidade", id: "inexistente", quantidade: 3 });
    expect(e.itens).toHaveLength(1);
  });

  it("adicionar o mesmo prato soma 1 (até 10) e limpar esvazia", () => {
    let e = reduzirCarrinho(vazio, { tipo: "adicionar", prato: prato("a") });
    e = reduzirCarrinho(e, { tipo: "adicionar", prato: prato("a") });
    expect(e.itens).toHaveLength(1);
    expect(e.itens[0].quantidade).toBe(2);
    e = reduzirCarrinho(e, { tipo: "alterarQuantidade", id: "a", quantidade: 10 });
    e = reduzirCarrinho(e, { tipo: "adicionar", prato: prato("a") });
    expect(e.itens[0].quantidade).toBe(10);
    expect(reduzirCarrinho(e, { tipo: "limpar" })).toEqual(vazio);
  });
});
