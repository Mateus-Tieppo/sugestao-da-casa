"use client";

import { useEffect, useReducer, useRef, useState, type ReactNode } from "react";
import { Ajuste } from "@/components/Ajuste";
import { Compositor } from "@/components/Compositor";
import { Carrinho } from "@/components/Carrinho";
import { Confirmacao } from "@/components/Confirmacao";
import { Cozinha, ID_CAMPO_PEDIDO, ID_TITULO } from "@/components/Cozinha";
import { Decisao } from "@/components/Decisao";
import { FalhaAmigavel } from "@/components/FalhaAmigavel";
import { ID_QUERO_ESSE } from "@/components/PratoPrincipal";
import { SemResultado } from "@/components/SemResultado";
import { TituloTela } from "@/components/TituloTela";
import { aquecer } from "@/lib/api";
import { reduzirCarrinho, type EstadoCarrinho } from "@/lib/carrinho";
import { formatarReais } from "@/lib/formato";
import { useSessao, type EstadoSessao } from "@/lib/sessao";
import type { PratoSugerido, RespostaSugestao } from "@/lib/tipos";

function anuncio(estado: EstadoSessao, confirmado: boolean): string {
  if (confirmado) return "Pedido simulado confirmado. Nada foi cobrado.";
  const { fase, resposta } = estado;
  if (fase === "pensando") return "Pensando na sua sugestão.";
  if (fase === "resultado" && resposta?.principal) {
    const p = resposta.principal;
    return `${resposta.frase_decisao ?? p.nome} ${formatarReais(p.total_centavos)} com entrega.`;
  }
  if (fase === "sem_resultado" || fase === "resultado") return "Não encontrei um prato com tudo isso.";
  if (fase === "falha") return "A cozinha não respondeu.";
  return "";
}

const PRATOS_DA_ABERTURA = (
  <div className="relative size-full">
    <div className="prato prato-grande prato-caldo chegada-prato size-full" />
    <div className="prato prato-curry chegada-acompanhamento absolute -left-[22%] bottom-[-14%] hidden size-[40%] md:block" />
    <div className="prato prato-pequeno prato-salada chegada-acompanhamento absolute -top-[6%] left-[-4%] hidden size-[22%] md:block" />
  </div>
);

export default function Home() {
  const { estado, enviar, removerEtiqueta, aceitarProposta, tentarDeNovo, escolherPrato, reiniciar } = useSessao();
  const { fase, resposta } = estado;
  const pensando = fase === "pensando";
  const frasePensando = estado.ultimoPedido?.texto ?? null;
  // Troca de alternativa feita na tela, anunciada enquanto a resposta for a mesma.
  const [troca, setTroca] = useState<{ de: RespostaSugestao; nome: string } | null>(null);
  const [carrinho, dispatchCarrinho] = useReducer(reduzirCarrinho, { itens: [] } satisfies EstadoCarrinho);
  const [carrinhoAberto, setCarrinhoAberto] = useState(false);
  const [confirmado, setConfirmado] = useState<EstadoCarrinho | null>(null);
  const devolverFoco = useRef(false);
  const faseAnterior = useRef(fase);

  useEffect(() => {
    aquecer();
  }, []);

  // Quando a tela muda, o foco vai junto: para o título da tela nova, ou para o campo ao voltar ao início.
  useEffect(() => {
    const antes = faseAnterior.current;
    faseAnterior.current = fase;
    if (fase === "resultado" || fase === "sem_resultado" || fase === "falha") {
      document.getElementById(ID_TITULO)?.focus();
    } else if (fase === "inicio" && antes !== "inicio") {
      document.getElementById(ID_CAMPO_PEDIDO)?.focus();
    }
  }, [fase, resposta]);

  useEffect(() => {
    if (confirmado) document.getElementById(ID_TITULO)?.focus();
  }, [confirmado]);

  // Ao fechar o carrinho sem confirmar, o foco volta ao botão que o abriu.
  useEffect(() => {
    if (!carrinhoAberto && devolverFoco.current) {
      devolverFoco.current = false;
      document.getElementById(ID_QUERO_ESSE)?.focus();
    }
  }, [carrinhoAberto]);

  function aoTrocar(prato: PratoSugerido) {
    escolherPrato(prato.id);
    if (resposta) setTroca({ de: resposta, nome: prato.nome });
  }

  function aoQuerer(prato: PratoSugerido) {
    dispatchCarrinho({ tipo: "limpar" });
    dispatchCarrinho({ tipo: "adicionar", prato });
    setCarrinhoAberto(true);
  }

  function fecharCarrinho() {
    devolverFoco.current = true;
    setCarrinhoAberto(false);
  }

  function confirmarPedido() {
    setConfirmado(carrinho);
    setCarrinhoAberto(false);
  }

  function recomecar() {
    dispatchCarrinho({ tipo: "limpar" });
    setConfirmado(null);
    reiniciar();
  }

  const aviso =
    fase === "resultado" && troca && troca.de === resposta
      ? `Agora a sugestão é ${troca.nome}.`
      : anuncio(estado, confirmado !== null);

  let tela: ReactNode;

  if (confirmado) {
    tela = <Confirmacao estado={confirmado} aoReiniciar={recomecar} />;
  } else if (resposta?.principal && resposta.status === "ok" && (fase === "resultado" || pensando)) {
    tela = (
      <Decisao resposta={resposta} aoQuerer={aoQuerer} aoTrocar={aoTrocar} pensando={pensando}>
        <Ajuste
          etiquetas={resposta.entendido}
          aoRemover={removerEtiqueta}
          aoEnviar={enviar}
          pensando={pensando}
          frasePensando={frasePensando}
        />
      </Decisao>
    );
  } else if (resposta && (fase === "sem_resultado" || fase === "resultado" || pensando)) {
    tela = (
      <SemResultado
        resposta={resposta}
        aoAceitar={aceitarProposta}
        aoRemover={removerEtiqueta}
        aoEnviar={enviar}
        pensando={pensando}
        frasePensando={frasePensando}
      />
    );
  } else if (fase === "falha") {
    tela = <FalhaAmigavel erro={estado.erro ?? "rede"} tentarDeNovo={tentarDeNovo} aoRecomecar={recomecar} />;
  } else {
    tela = (
      <Cozinha
        ocupado={pensando}
        topo={
          <TituloTela
            titulo={
              <>
                Diga a vontade. <em className="text-acafrao">A casa decide.</em>
              </>
            }
            texto="Escreva como falaria com o garçom. A gente escolhe um prato do cardápio e conta o porquê."
          />
        }
        prato={
          <div aria-hidden="true" className={`size-full ${pensando ? "girando" : ""}`}>
            {PRATOS_DA_ABERTURA}
          </div>
        }
      >
        <div className="chegada-cartao">
          <Compositor aoEnviar={enviar} pensando={pensando} frasePensando={frasePensando} />
        </div>
      </Cozinha>
    );
  }

  return (
    <main className="flex flex-1 flex-col">
      {tela}
      {carrinhoAberto ? (
        <Carrinho
          estado={carrinho}
          aoAlterarQuantidade={(id, quantidade) => dispatchCarrinho({ tipo: "alterarQuantidade", id, quantidade })}
          aoConfirmar={confirmarPedido}
          aoFechar={fecharCarrinho}
        />
      ) : null}
      <p aria-live="polite" className="sr-only">
        {aviso}
      </p>
    </main>
  );
}
