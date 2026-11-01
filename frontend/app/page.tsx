"use client";

import { useEffect, type ReactNode } from "react";
import { Ajuste } from "@/components/Ajuste";
import { Compositor } from "@/components/Compositor";
import { Cozinha } from "@/components/Cozinha";
import { Decisao } from "@/components/Decisao";
import { aquecer } from "@/lib/api";
import { formatarReais } from "@/lib/formato";
import { useSessao, type EstadoSessao } from "@/lib/sessao";
import type { PratoSugerido } from "@/lib/tipos";

// O carrinho chega na próxima etapa; por enquanto "Quero esse" não leva a lugar nenhum.
function aoQuerer(prato: PratoSugerido) {
  void prato;
}

function anuncio(estado: EstadoSessao): string {
  const { fase, resposta } = estado;
  if (fase === "pensando") return "Pensando na sua sugestão.";
  if (fase === "resultado" && resposta?.principal) {
    const p = resposta.principal;
    return `${resposta.frase_decisao ?? p.nome} ${formatarReais(p.total_centavos)} com entrega.`;
  }
  if (fase === "sem_resultado") return "Não encontrei um prato com tudo isso.";
  if (fase === "falha") return "A cozinha não respondeu.";
  return "";
}

const PRATOS_DA_ABERTURA = (
  <div className="relative size-full">
    <div className="prato prato-grande prato-caldo size-full" />
    <div className="prato prato-curry absolute -left-[22%] bottom-[-14%] hidden size-[40%] md:block" />
    <div className="prato prato-pequeno prato-salada absolute -top-[6%] left-[-4%] hidden size-[22%] md:block" />
  </div>
);

function TituloSimples({ titulo, texto }: { titulo: ReactNode; texto: string }) {
  return (
    <>
      <h1 className="font-titulo text-[2.125rem] font-normal leading-[1.04] tracking-[-0.025em] text-balance sm:text-[2.75rem] md:text-[4rem]">
        {titulo}
      </h1>
      <p className="mt-3 max-w-[38ch] text-[0.9375rem] leading-snug text-creme-rosado md:mt-5 md:text-[1.0625rem]">
        {texto}
      </p>
    </>
  );
}

export default function Home() {
  const { estado, enviar, removerEtiqueta, tentarDeNovo, escolherPrato } = useSessao();
  const { fase, resposta } = estado;
  const pensando = fase === "pensando";
  const frasePensando = estado.ultimoPedido?.texto ?? null;

  useEffect(() => {
    aquecer();
  }, []);

  let tela: ReactNode;

  if (resposta && resposta.status === "ok" && (fase === "resultado" || pensando)) {
    tela = (
      <Decisao resposta={resposta} aoQuerer={aoQuerer} aoTrocar={(p) => escolherPrato(p.id)} pensando={pensando}>
        <Ajuste
          etiquetas={resposta.entendido}
          aoRemover={removerEtiqueta}
          aoEnviar={enviar}
          pensando={pensando}
          frasePensando={frasePensando}
        />
      </Decisao>
    );
  } else if (resposta && (fase === "sem_resultado" || pensando)) {
    // Provisório: a tela caprichada de "sem resultado" vem na próxima etapa.
    tela = (
      <Cozinha
        topo={
          <TituloSimples
            titulo="Com tudo isso junto, não achei."
            texto={resposta.proposta?.mensagem ?? "Tente tirar alguma exigência."}
          />
        }
        prato={<div className="prato prato-grande prato-caldo size-full opacity-80" />}
      >
        <div className="rounded-2xl bg-cartao p-5 shadow-[0_22px_44px_-18px_rgb(90_30_10/0.35)] sm:p-7">
          <Ajuste
            etiquetas={resposta.entendido}
            aoRemover={removerEtiqueta}
            aoEnviar={enviar}
            pensando={pensando}
            frasePensando={frasePensando}
          />
        </div>
      </Cozinha>
    );
  } else if (fase === "falha") {
    // Provisório: a tela caprichada de falha vem na próxima etapa.
    tela = (
      <Cozinha
        topo={
          <TituloSimples
            titulo="A cozinha não respondeu."
            texto="Às vezes ela demora para acordar. Tente de novo em instantes."
          />
        }
        prato={<div className="prato prato-grande prato-caldo size-full" />}
      >
        <div className="rounded-2xl bg-cartao p-5 shadow-[0_22px_44px_-18px_rgb(90_30_10/0.35)] sm:p-7">
          <button
            type="button"
            onClick={tentarDeNovo}
            className="flex h-[3.25rem] w-full items-center justify-center rounded-xl bg-tomate font-semibold text-[#fff8ec] transition-colors duration-200 hover:bg-tomate-escuro"
          >
            Tentar de novo
          </button>
        </div>
      </Cozinha>
    );
  } else {
    tela = (
      <Cozinha
        topo={
          <TituloSimples
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
        <Compositor aoEnviar={enviar} pensando={pensando} frasePensando={frasePensando} />
      </Cozinha>
    );
  }

  return (
    <main className="flex flex-1 flex-col">
      {tela}
      <p aria-live="polite" className="sr-only">
        {anuncio(estado)}
      </p>
    </main>
  );
}
