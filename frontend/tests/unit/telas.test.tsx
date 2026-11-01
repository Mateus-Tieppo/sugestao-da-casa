import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import Home from "@/app/page";
import { describe, expect, it, vi } from "vitest";
import { Compositor } from "@/components/Compositor";
import { Decisao } from "@/components/Decisao";
import { Entendido } from "@/components/Entendido";
import { FotoPrato } from "@/components/FotoPrato";
import { SeloDemonstracao } from "@/components/SeloDemonstracao";
import type { RespostaSugestao } from "@/lib/tipos";
import { prato, respostaOk } from "./fixtures";

function respostaCompleta(): RespostaSugestao {
  return {
    ...respostaOk("caldo"),
    frase_decisao: "Hoje pede um Caldo verde.",
    principal: { ...prato("caldo"), nome: "Caldo verde", total_centavos: 3200, etiquetas: ["sem lactose", "25 min"] },
    alternativas: [
      { ...prato("lamen"), nome: "Lámen shoyu", total_centavos: 3800, diferenca: "mais salgadinho" },
      { ...prato("curry"), nome: "Curry de coco", total_centavos: 3600, diferenca: "um toque de picância" },
    ],
  };
}

describe("Compositor", () => {
  it("exemplo clicável envia a frase", () => {
    const aoEnviar = vi.fn();
    render(<Compositor aoEnviar={aoEnviar} pensando={false} />);
    fireEvent.click(screen.getByRole("button", { name: /algo quentinho, não muito pesado, até R\$ 40, sem lactose/ }));
    expect(aoEnviar).toHaveBeenCalledWith("algo quentinho, não muito pesado, até R$ 40, sem lactose");
  });

  it("botão de enviar fica desabilitado com texto vazio e Enter envia", () => {
    const aoEnviar = vi.fn();
    render(<Compositor aoEnviar={aoEnviar} pensando={false} />);
    const enviar = screen.getByRole("button", { name: "Pedir sugestão" });
    expect(enviar).toBeDisabled();
    const campo = screen.getByRole("textbox", { name: /o que você quer comer/i });
    fireEvent.change(campo, { target: { value: "algo leve" } });
    expect(enviar).toBeEnabled();
    fireEvent.keyDown(campo, { key: "Enter" });
    expect(aoEnviar).toHaveBeenCalledWith("algo leve");
  });
});

describe("Decisao", () => {
  it("resultado mostra decisão, principal e duas alternativas", () => {
    render(<Decisao resposta={respostaCompleta()} aoQuerer={vi.fn()} />);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Hoje pede um Caldo verde.");
    const principal = screen.getByRole("article", { name: "Caldo verde" });
    expect(within(principal).getByText("R$ 32")).toBeInTheDocument();
    expect(within(principal).getByRole("button", { name: "Quero esse" })).toBeInTheDocument();
    const alternativas = screen.getByRole("list", { name: "Ou, se preferir" });
    expect(within(alternativas).getAllByRole("listitem")).toHaveLength(2);
    expect(within(alternativas).getByText(/mais salgadinho/)).toBeInTheDocument();
    expect(within(alternativas).getByText(/um toque de picância/)).toBeInTheDocument();
  });

  it("clicar na alternativa promove sem chamar a API", () => {
    const fetch = vi.fn();
    vi.stubGlobal("fetch", fetch);
    const aoQuerer = vi.fn();
    const aoTrocar = vi.fn();
    render(<Decisao resposta={respostaCompleta()} aoQuerer={aoQuerer} aoTrocar={aoTrocar} />);
    fireEvent.click(screen.getByRole("button", { name: /Lámen shoyu/ }));
    const principal = screen.getByRole("article", { name: "Lámen shoyu" });
    expect(within(principal).getByText("R$ 38")).toBeInTheDocument();
    const alternativas = screen.getByRole("list", { name: "Ou, se preferir" });
    expect(within(alternativas).getByText("Caldo verde")).toBeInTheDocument();
    fireEvent.click(within(principal).getByRole("button", { name: "Quero esse" }));
    expect(aoQuerer).toHaveBeenCalledWith(expect.objectContaining({ id: "lamen" }));
    expect(aoTrocar).toHaveBeenCalledWith(expect.objectContaining({ id: "lamen" }));
    expect(fetch).not.toHaveBeenCalled();
    vi.unstubAllGlobals();
  });
});

describe("SeloDemonstracao", () => {
  it("selo aparece só no modo demonstração", () => {
    const texto = "Modo demonstração: respostas mais simples enquanto a IA descansa.";
    const { rerender } = render(<SeloDemonstracao modo="demonstracao" />);
    expect(screen.getByText(texto)).toBeInTheDocument();
    rerender(<SeloDemonstracao modo="ia" />);
    expect(screen.queryByText(texto)).not.toBeInTheDocument();
  });
});

describe("Entendido", () => {
  it("remover etiqueta chama aoRemover com a chave", () => {
    const aoRemover = vi.fn();
    render(
      <Entendido
        etiquetas={[
          { chave: "orcamento", rotulo: "até R$ 30" },
          { chave: "restricao:sem_lactose", rotulo: "sem lactose" },
        ]}
        aoRemover={aoRemover}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Remover sem lactose" }));
    expect(aoRemover).toHaveBeenCalledWith("restricao:sem_lactose");
  });
});

function servirResposta(resposta: RespostaSugestao) {
  const fetch = vi.fn((url: string) =>
    Promise.resolve(
      url.endsWith("/health")
        ? new Response("{}", { status: 200 })
        : new Response(JSON.stringify(resposta), { status: 200 }),
    ),
  );
  vi.stubGlobal("fetch", fetch);
  return fetch;
}

describe("Home", () => {
  it("move o foco para o título quando o resultado chega e anuncia a troca", async () => {
    servirResposta(respostaCompleta());
    render(<Home />);
    fireEvent.click(screen.getByRole("button", { name: /fresquinho e rápido/ }));
    const titulo = await screen.findByRole("heading", { level: 1, name: "Hoje pede um Caldo verde." });
    await waitFor(() => expect(titulo).toHaveFocus());
    fireEvent.click(screen.getByRole("button", { name: /Lámen shoyu/ }));
    expect(screen.getByText("Agora a sugestão é Lámen shoyu.")).toBeInTheDocument();
    vi.unstubAllGlobals();
  });

  it("status ok sem prato principal cai na tela de sem resultado", async () => {
    servirResposta({ ...respostaCompleta(), principal: null, alternativas: [] });
    render(<Home />);
    fireEvent.click(screen.getByRole("button", { name: /fresquinho e rápido/ }));
    const titulo = await screen.findByRole("heading", { level: 1, name: "Com tudo isso junto, não achei." });
    await waitFor(() => expect(titulo).toHaveFocus());
    vi.unstubAllGlobals();
  });
});

describe("FotoPrato", () => {
  it("usa o prato ilustrado quando a foto não é do Unsplash", () => {
    const { container, rerender } = render(
      <FotoPrato nome="Caldo" fotoUrl="https://exemplo.com/caldo.jpg" tamanho="medio" sizes="56px" />,
    );
    expect(container.querySelector("img")).toBeNull();
    expect(container.firstChild).toHaveClass("prato-caldo");
    rerender(
      <FotoPrato nome="Caldo" fotoUrl="https://images.unsplash.com/photo-1?w=800" tamanho="medio" sizes="56px" />,
    );
    expect(container.querySelector("img")).not.toBeNull();
  });
});
