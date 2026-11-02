import { expect, test, type Page } from "@playwright/test";
import {
  COMO_DEMONSTRACAO,
  DEPOIS_DA_PROPOSTA,
  EXEMPLO,
  MAIS_BARATO,
  PRIMEIRA,
  SEM_ETIQUETA,
  SEM_RESULTADO,
  interceptarApi,
} from "./mocks";

async function pedirExemplo(page: Page) {
  await page.goto("/");
  await page.getByRole("button", { name: EXEMPLO }).click();
}

test("fluxo principal: pedir, ver a decisão, remover etiqueta, refinar, pedir e confirmar", async ({ page }) => {
  const api = await interceptarApi(page, (pedido, n) => {
    if (n === 1) return PRIMEIRA;
    if (pedido.texto === "mais barato") return MAIS_BARATO;
    return SEM_ETIQUETA;
  });

  await pedirExemplo(page);
  await expect(page.getByText("Lendo sua vontade…")).toBeVisible();

  const titulo = page.getByRole("heading", { level: 1 });
  await expect(titulo).toContainText("Hoje pede um Caldo verde.");
  await expect(page.getByRole("article", { name: "Caldo verde" })).toContainText("R$ 32");
  await expect(page.getByText("Modo demonstração")).toHaveCount(0);
  expect(api.pedidos[0]).toMatchObject({ texto: EXEMPLO, criterios: null, prato_atual_id: null });

  // Remover uma etiqueta refaz o pedido com os critérios sem ela.
  await page.getByRole("button", { name: "Remover sem lactose" }).click();
  await expect(page.getByRole("button", { name: "Remover sem lactose" })).toHaveCount(0);
  expect(api.pedidos[1].texto).toBeNull();
  expect(api.pedidos[1].criterios?.restricoes).toEqual([]);

  // Refinar em texto leva o prato atual como referência.
  await page.getByLabel("Quer ajustar?").fill("mais barato");
  await page.getByRole("button", { name: "Ajustar" }).click();
  await expect(titulo).toContainText("Sopa de abóbora");
  expect(api.pedidos[2]).toMatchObject({ texto: "mais barato", prato_atual_id: "caldo" });
  await expect(page.getByRole("article", { name: "Sopa de abóbora" })).toContainText("R$ 22");

  await page.getByRole("button", { name: "Quero esse" }).click();
  const carrinho = page.getByRole("dialog", { name: "Seu pedido" });
  await expect(carrinho).toBeVisible();
  await expect(carrinho).toContainText("Sopa de abóbora");
  await carrinho.getByRole("button", { name: "Confirmar pedido" }).click();

  await expect(page.getByText("Pedido simulado: nada foi cobrado")).toBeVisible();
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Pedido feito.");
  await expect(carrinho).toHaveCount(0);
});

test("sem resultado com proposta aceita", async ({ page }) => {
  const api = await interceptarApi(page, (_pedido, n) => (n === 1 ? SEM_RESULTADO : DEPOIS_DA_PROPOSTA));

  await pedirExemplo(page);
  await expect(page.getByRole("heading", { level: 1 })).toContainText("não achei");
  await expect(page.getByText("Com R$\u00a024 e 30 min, o Risoto de cogumelos serve.")).toBeVisible();

  await page.getByRole("button", { name: "Subir para R$\u00a024 e esperar 30 min" }).click();
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Hoje pede um Risoto de cogumelos.");
  expect(api.pedidos[1].texto).toBeNull();
  expect(api.pedidos[1].criterios).toMatchObject({ orcamento_max_centavos: 2400, tempo_max_min: 30 });
  await expect(page.getByRole("article", { name: "Risoto de cogumelos" })).toContainText("R$ 24");
});

test("modo demonstração mostra o selo", async ({ page }) => {
  await interceptarApi(page, () => COMO_DEMONSTRACAO(PRIMEIRA));
  await pedirExemplo(page);
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Caldo verde");
  await expect(page.getByText("Modo demonstração: respostas mais simples enquanto a IA descansa.")).toBeVisible();
});

test.describe("reduced motion", () => {
  test.use({ reducedMotion: "reduce" });

  test("o resultado aparece sem animação de transform", async ({ page }) => {
    await interceptarApi(page, () => PRIMEIRA);
    await page.goto("/");
    // Amostra, a cada quadro, o transform de tudo que a entrada costuma animar.
    await page.evaluate(() => {
      const w = window as unknown as { __transforms: string[] };
      w.__transforms = [];
      const amostrar = () => {
        document.querySelectorAll("[data-entrada]").forEach((el) => {
          w.__transforms.push(getComputedStyle(el).transform);
        });
        requestAnimationFrame(amostrar);
      };
      requestAnimationFrame(amostrar);
    });

    await page.getByRole("button", { name: EXEMPLO }).click();
    await expect(page.getByRole("heading", { level: 1 })).toContainText("Caldo verde");
    await page.waitForTimeout(1200);

    const amostras = await page.evaluate(() => (window as unknown as { __transforms: string[] }).__transforms);
    expect(amostras.length).toBeGreaterThan(0);
    expect(new Set(amostras)).toEqual(new Set(["none"]));
  });
});

test("carrinho: o foco fica preso no diálogo e Escape devolve o foco a 'Quero esse'", async ({ page }) => {
  await interceptarApi(page, () => PRIMEIRA, 50);
  await pedirExemplo(page);
  const quero = page.getByRole("button", { name: "Quero esse" });
  await quero.click();
  const carrinho = page.getByRole("dialog", { name: "Seu pedido" });
  await expect(carrinho).toBeVisible();

  // Num <dialog> modal o Tab pode sair para a interface do navegador (activeElement vira o body),
  // mas nunca chega ao conteúdo atrás: a cada volta o foco é sempre do diálogo ou do body.
  const ondeEstaOFoco = () =>
    page.evaluate(() => {
      const a = document.activeElement;
      if (a === document.body) return "navegador";
      return document.querySelector("dialog")?.contains(a) ? "dialogo" : "pagina";
    });

  for (const tecla of ["Tab", "Shift+Tab"]) {
    const visto = new Set<string>();
    for (let i = 0; i < 12; i++) {
      await page.keyboard.press(tecla);
      visto.add(await ondeEstaOFoco());
    }
    expect(visto.has("pagina")).toBe(false);
    expect(visto.has("dialogo")).toBe(true);
  }
  // Volta para dentro do diálogo antes de fechar.
  await carrinho.getByRole("button", { name: "Fechar o pedido" }).focus();

  await page.keyboard.press("Escape");
  await expect(carrinho).toHaveCount(0);
  await expect(quero).toBeFocused();
});
