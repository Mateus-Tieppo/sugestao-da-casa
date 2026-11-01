"use client";

import { useState, type ReactNode } from "react";
import type { PratoSugerido, RespostaSugestao } from "@/lib/tipos";
import { Alternativas } from "./Alternativas";
import { Cozinha, ID_TITULO } from "./Cozinha";
import { FotoPrato } from "./FotoPrato";
import { PratoPrincipal } from "./PratoPrincipal";
import { SeloDemonstracao } from "./SeloDemonstracao";

const ABERTURA = /^(Hoje pede (?:um|uma) )(.+)$/;

/** "Hoje pede um caldo verde." com o prato em destaque, como no mockup. */
function FraseDecisao({ frase }: { frase: string }) {
  const m = ABERTURA.exec(frase);
  if (!m) return <>{frase}</>;
  return (
    <>
      {m[1]}
      <em className="text-acafrao">{m[2]}</em>
    </>
  );
}

/** "Do jeito que você pediu: sem lactose, até R$ 40 e leve." */
function porque(resposta: RespostaSugestao, principal: PratoSugerido): string {
  const r = resposta.entendido.map((e) => e.rotulo);
  if (r.length === 0) return `${principal.restaurante} · chega em ${principal.tempo_min} min`;
  const lista = r.length === 1 ? r[0] : `${r.slice(0, -1).join(", ")} e ${r[r.length - 1]}`;
  return `Do jeito que você pediu: ${lista}.`;
}

function tamanhoDoTitulo(frase: string): string {
  if (frase.length > 46) return "text-[1.625rem] sm:text-[2.25rem] md:text-[3rem]";
  if (frase.length > 32) return "text-[1.875rem] sm:text-[2.5rem] md:text-[3.5rem]";
  return "text-[2.125rem] sm:text-[2.75rem] md:text-[4rem]";
}

interface Props {
  resposta: RespostaSugestao;
  aoQuerer: (prato: PratoSugerido) => void;
  /** A pessoa promoveu outro prato a principal (sem nova chamada à API). */
  aoTrocar?: (prato: PratoSugerido) => void;
  /** A cozinha está refazendo a sugestão: o resultado atual fica esmaecido. */
  pensando?: boolean;
  /** Vem embaixo do cartão principal (etiquetas e campo de ajuste). */
  children?: ReactNode;
}

/** Tela de resultado: a decisão no bloco quente, o cartão do prato e duas alternativas. */
export function Decisao({ resposta, aoQuerer, aoTrocar, pensando = false, children }: Props) {
  // A escolha local vale só para esta resposta; uma resposta nova volta à escolha da casa.
  const [escolha, setEscolha] = useState<{ de: RespostaSugestao; id: string | null }>({ de: resposta, id: null });
  if (escolha.de !== resposta) setEscolha({ de: resposta, id: null });
  const idEscolhido = escolha.de === resposta ? escolha.id : null;

  const daCasa = resposta.principal;
  if (!daCasa) return null;
  const todos = [daCasa, ...resposta.alternativas];
  const principal = todos.find((p) => p.id === idEscolhido) ?? daCasa;
  const alternativas = todos.filter((p) => p.id !== principal.id);
  const trocou = principal.id !== daCasa.id;

  const frase = trocou ? `Então vai de ${principal.nome}.` : (resposta.frase_decisao ?? principal.nome);
  const esmaecido = `transition-opacity duration-300 ease-saida ${pensando ? "opacity-60" : ""}`;

  return (
    <Cozinha
      topo={
        <div className={esmaecido}>
          <h1
            id={ID_TITULO}
            tabIndex={-1}
            className={`font-titulo font-normal outline-none leading-[1.04] tracking-[-0.025em] text-balance ${tamanhoDoTitulo(frase)}`}
          >
            {trocou ? (
              <>
                Então vai de <em className="text-acafrao">{principal.nome}.</em>
              </>
            ) : (
              <FraseDecisao frase={frase} />
            )}
          </h1>
          <p className="mt-3 max-w-[40ch] text-[0.9375rem] leading-snug text-creme-rosado md:mt-5 md:text-[1.0625rem]">
            {porque(resposta, principal)}
          </p>
        </div>
      }
      prato={
        <FotoPrato
          key={principal.id}
          nome={principal.nome}
          fotoUrl={principal.foto_url}
          tamanho="grande"
          sizes="(min-width: 1024px) 368px, (min-width: 768px) 336px, (min-width: 640px) 208px, 156px"
          preload
          className={`size-full ${pensando ? "girando" : ""}`}
        />
      }
      rodape={children}
      lateral={
        <div className={esmaecido}>
          <Alternativas
            pratos={alternativas}
            escolhaDaCasaId={daCasa.id}
            aoEscolher={(p) => {
              setEscolha({ de: resposta, id: p.id });
              aoTrocar?.(p);
            }}
          />
        </div>
      }
    >
      <PratoPrincipal prato={principal} aoQuerer={aoQuerer} esmaecido={pensando} />
      <div className="mt-5 px-1">
        <SeloDemonstracao modo={resposta.modo} />
      </div>
    </Cozinha>
  );
}
