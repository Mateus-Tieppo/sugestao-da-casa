import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import Home from "@/app/page";
import { Carrinho } from "@/components/Carrinho";
import { Confirmacao } from "@/components/Confirmacao";
import { FalhaAmigavel } from "@/components/FalhaAmigavel";
import { SemResultado } from "@/components/SemResultado";
import { reduzirCarrinho } from "@/lib/carrinho";
import type { MudancaSugerida, PropostaSugerida, RespostaSugestao } from "@/lib/tipos";
import { prato, respostaOk } from "./fixtures";

afterEach(() => vi.unstubAllGlobals());

const MUDANCA_ORCAMENTO: MudancaSugerida = { campo: "orcamento", valor_atual: 1500, valor_sugerido: 1900 };
const MUDANCA_TEMPO: MudancaSugerida = { campo: "tempo", valor_atual: 10, valor_sugerido: 15 };

function semResultado(mudancas: MudancaSugerida[] | null): RespostaSugestao {
  const proposta: PropostaSugerida | null = mudancas && {
    mudancas,
    mensagem: "Com um pouco mais de verba aparece um prato bom.",
    prato: { ...prato("caldo"), nome: "Caldo verde", total_centavos: 1900 },
  };
  return { ...respostaOk("x"), status: "sem_resultado", principal: null, alternativas: [], frase_decisao: null, proposta };
}

function renderSemResultado(resposta: RespostaSugestao, aoAceitar = vi.fn()) {
  render(
    <SemResultado
      resposta={resposta}
      aoAceitar={aoAceitar}
      aoRemover={vi.fn()}
      aoEnviar={vi.fn()}
      pensando={false}
      frasePensando={null}
    />,
  );
  return aoAceitar;
}

describe("SemResultado", () => {
  it("sem resultado mostra a proposta e o botão de aceitar", () => {
    const aoAceitar = renderSemResultado(semResultado([{ campo: "orcamento", valor_atual: 1500, valor_sugerido: 2200 }]));
    expect(screen.getByText("Com um pouco mais de verba aparece um prato bom.")).toBeInTheDocument();
    expect(screen.getByText("Caldo verde")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Subir para R$\u00a022" }));
    expect(aoAceitar).toHaveBeenCalledTimes(1);
  });

  it("o botão reflete todas as mudanças da proposta", () => {
    renderSemResultado(semResultado([MUDANCA_ORCAMENTO, MUDANCA_TEMPO]));
    expect(screen.getByRole("button", { name: "Subir para R$\u00a019 e esperar 15 min" })).toBeInTheDocument();
  });

  it("proposta só de tempo vira 'Esperar até 15 min'", () => {
    renderSemResultado(semResultado([MUDANCA_TEMPO]));
    expect(screen.getByRole("button", { name: "Esperar até 15 min" })).toBeInTheDocument();
  });

  it("sem resultado e sem proposta pede para ajustar a frase", () => {
    renderSemResultado(semResultado(null));
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Com tudo isso junto, não achei.");
    expect(screen.getByText(/tire alguma exigência ou escreva de outro jeito/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /subir|esperar/i })).not.toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Quer ajustar?" })).toBeInTheDocument();
  });
});

describe("FalhaAmigavel", () => {
  it("falha amigável oferece tentar de novo e chama tentarDeNovo", () => {
    const tentarDeNovo = vi.fn();
    render(<FalhaAmigavel erro="timeout" tentarDeNovo={tentarDeNovo} />);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("A cozinha não respondeu.");
    fireEvent.click(screen.getByRole("button", { name: "Tentar de novo" }));
    expect(tentarDeNovo).toHaveBeenCalledTimes(1);
  });

  it("explica cada tipo de falha com palavras simples", () => {
    const { rerender } = render(<FalhaAmigavel erro="timeout" tentarDeNovo={vi.fn()} />);
    expect(screen.getByText(/demorou mais do que devia/i)).toBeInTheDocument();
    rerender(<FalhaAmigavel erro="rede" tentarDeNovo={vi.fn()} />);
    expect(screen.getByText(/sem conexão/i)).toBeInTheDocument();
    rerender(<FalhaAmigavel erro="servidor" tentarDeNovo={vi.fn()} />);
    expect(screen.getByText(/tropeçou/i)).toBeInTheDocument();
  });
});

const estadoComUm = () => reduzirCarrinho({ itens: [] }, { tipo: "adicionar", prato: { ...prato("a"), nome: "Caldo verde" } });

describe("Carrinho", () => {
  it("é um diálogo modal com nome, quantidade e total", () => {
    const aoAlterar = vi.fn();
    const aoConfirmar = vi.fn();
    render(<Carrinho estado={estadoComUm()} aoAlterarQuantidade={aoAlterar} aoConfirmar={aoConfirmar} aoFechar={vi.fn()} />);
    const dialogo = screen.getByRole("dialog", { name: "Seu pedido" });
    expect(dialogo).toHaveAttribute("aria-modal", "true");
    expect(within(dialogo).getByText("Caldo verde")).toBeInTheDocument();
    expect(within(dialogo).getByText("Entrega")).toBeInTheDocument();
    expect(within(dialogo).getByTestId("total")).toHaveTextContent("R$ 30");
    fireEvent.click(within(dialogo).getByRole("button", { name: "Aumentar quantidade de Caldo verde" }));
    expect(aoAlterar).toHaveBeenCalledWith("a", 2);
    fireEvent.click(within(dialogo).getByRole("button", { name: "Confirmar pedido" }));
    expect(aoConfirmar).toHaveBeenCalledTimes(1);
  });

  it("os botões de quantidade respeitam o mínimo e o máximo", () => {
    const aoAlterar = vi.fn();
    const base = estadoComUm();
    const { rerender } = render(
      <Carrinho estado={base} aoAlterarQuantidade={aoAlterar} aoConfirmar={vi.fn()} aoFechar={vi.fn()} />,
    );
    expect(screen.getByRole("button", { name: "Diminuir quantidade de Caldo verde" })).toBeDisabled();
    const cheio = reduzirCarrinho(base, { tipo: "alterarQuantidade", id: "a", quantidade: 10 });
    rerender(<Carrinho estado={cheio} aoAlterarQuantidade={aoAlterar} aoConfirmar={vi.fn()} aoFechar={vi.fn()} />);
    expect(screen.getByRole("button", { name: "Aumentar quantidade de Caldo verde" })).toBeDisabled();
  });

  it("Escape (evento cancel) e o botão de fechar chamam aoFechar", () => {
    const aoFechar = vi.fn();
    render(<Carrinho estado={estadoComUm()} aoAlterarQuantidade={vi.fn()} aoConfirmar={vi.fn()} aoFechar={aoFechar} />);
    const dialogo = screen.getByRole("dialog");
    fireEvent(dialogo, new Event("cancel", { cancelable: true }));
    expect(aoFechar).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole("button", { name: "Fechar o pedido" }));
    expect(aoFechar).toHaveBeenCalledTimes(2);
  });
});

describe("Confirmacao", () => {
  it("diz que o pedido é simulado, mostra o tempo e volta ao início", () => {
    const aoReiniciar = vi.fn();
    render(<Confirmacao estado={estadoComUm()} aoReiniciar={aoReiniciar} />);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(/bom apetite/i);
    expect(screen.getByText("Pedido simulado: nada foi cobrado")).toBeInTheDocument();
    expect(screen.getByText(/30 min/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Pedir outra coisa" }));
    expect(aoReiniciar).toHaveBeenCalledTimes(1);
  });
});

function servir(respostas: RespostaSugestao[]) {
  let i = 0;
  const fetch = vi.fn((url: string, init?: RequestInit) => {
    void init;
    return Promise.resolve(
      url.endsWith("/health")
        ? new Response("{}", { status: 200 })
        : new Response(JSON.stringify(respostas[Math.min(i++, respostas.length - 1)]), { status: 200 }),
    );
  });
  vi.stubGlobal("fetch", fetch);
  return fetch;
}

describe("Home: do resultado ao pedido simulado", () => {
  it("Quero esse abre o carrinho, confirma, e Pedir outra coisa volta ao início", async () => {
    servir([{ ...respostaOk("caldo"), principal: { ...prato("caldo"), nome: "Caldo verde" } }]);
    render(<Home />);
    fireEvent.click(screen.getByRole("button", { name: /fresquinho e rápido/ }));
    await screen.findByRole("heading", { level: 1 });
    fireEvent.click(await screen.findByRole("button", { name: "Quero esse" }));
    const dialogo = screen.getByRole("dialog", { name: "Seu pedido" });
    fireEvent.click(within(dialogo).getByRole("button", { name: "Confirmar pedido" }));
    const titulo = await screen.findByRole("heading", { level: 1, name: /bom apetite/i });
    await waitFor(() => expect(titulo).toHaveFocus());
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(screen.getByText("Pedido simulado: nada foi cobrado")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Pedir outra coisa" }));
    const campo = await screen.findByRole("textbox", { name: /o que você quer comer/i });
    await waitFor(() => expect(campo).toHaveFocus());
  });

  it("fechar o carrinho devolve o foco ao botão Quero esse", async () => {
    servir([{ ...respostaOk("caldo"), principal: { ...prato("caldo"), nome: "Caldo verde" } }]);
    render(<Home />);
    fireEvent.click(screen.getByRole("button", { name: /fresquinho e rápido/ }));
    const quero = await screen.findByRole("button", { name: "Quero esse" });
    fireEvent.click(quero);
    fireEvent.click(screen.getByRole("button", { name: "Fechar o pedido" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(quero).toHaveFocus();
  });

  it("aceitar a proposta refaz o pedido com as mudanças e mostra o prato", async () => {
    const fetch = servir([
      semResultado([MUDANCA_ORCAMENTO]),
      { ...respostaOk("caldo"), principal: { ...prato("caldo"), nome: "Caldo verde" } },
    ]);
    render(<Home />);
    fireEvent.click(screen.getByRole("button", { name: /fresquinho e rápido/ }));
    const aceitar = await screen.findByRole("button", { name: "Subir para R$\u00a019" });
    fireEvent.click(aceitar);
    await screen.findByRole("article", { name: "Caldo verde" });
    const corpos = fetch.mock.calls
      .filter(([u]) => String(u).endsWith("/v1/sugestoes"))
      .map(([, init]) => JSON.parse((init as RequestInit).body as string));
    expect(corpos[1].criterios.orcamento_max_centavos).toBe(1900);
    expect(corpos[1].texto).toBeNull();
  });

  it("falha da API mostra a tela amigável e Tentar de novo reenvia", async () => {
    const fetch = vi.fn((url: string) =>
      Promise.resolve(url.endsWith("/health") ? new Response("{}") : new Response("{}", { status: 500 })),
    );
    vi.stubGlobal("fetch", fetch);
    render(<Home />);
    fireEvent.click(screen.getByRole("button", { name: /fresquinho e rápido/ }));
    const titulo = await screen.findByRole("heading", { level: 1, name: "A cozinha não respondeu." });
    await waitFor(() => expect(titulo).toHaveFocus());
    fireEvent.click(screen.getByRole("button", { name: "Tentar de novo" }));
    await waitFor(() =>
      expect(fetch.mock.calls.filter(([u]) => String(u).endsWith("/v1/sugestoes"))).toHaveLength(2),
    );
  });
});
