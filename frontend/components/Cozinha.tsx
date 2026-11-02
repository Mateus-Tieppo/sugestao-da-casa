"use client";

import { useEffect, useRef, type ReactNode } from "react";
import { EASE_CHEGADA, EASE_SUAVE, comMovimento, gsap, useGSAP } from "@/lib/movimento";
import { Vapor } from "./Vapor";

/** O h1 de cada tela recebe o foco quando a tela muda (teclado e leitor de tela). */
export const ID_TITULO = "titulo-tela";
/** O campo principal do pedido, focado ao voltar para o início. */
export const ID_CAMPO_PEDIDO = "campo-pedido";

interface Props {
  /** O h1 e o que vem logo abaixo dele, dentro do bloco quente. */
  topo: ReactNode;
  /** O prato em destaque, à direita do bloco quente. */
  prato: ReactNode;
  /** Coluna principal: começa sobreposta à borda do bloco quente. */
  children: ReactNode;
  /** Coluna lateral no desktop, embaixo do prato; no celular vem depois da principal. */
  lateral?: ReactNode;
  /** Embaixo da coluna principal no desktop; no celular vem por último. */
  rodape?: ReactNode;
  /**
   * Muda quando chega conteúdo novo (uma resposta, uma falha): a tela entra coreografada.
   * Sem chave, nada anima por JS (o início usa só a entrada em CSS, que não depende de script).
   */
  chaveEntrada?: unknown;
  /** Muda quando a pessoa troca o prato na mesma resposta: só o prato e o cartão se acomodam. */
  chaveTroca?: unknown;
  /** A cozinha está pensando: a entrada em curso termina na hora e o prato solta vapor. */
  ocupado?: boolean;
}

/**
 * A "cozinha aberta": bloco páprica no topo, prato em destaque e um cartão creme
 * que sobe por cima da borda. Início e resultado usam o mesmo esqueleto,
 * então a troca de tela não muda o desenho da página.
 *
 * Movimento: só transform e opacity (nada muda de tamanho ou lugar no layout), nunca
 * visibility (o h1 precisa poder receber foco no mesmo instante em que chega).
 */
export function Cozinha({ topo, prato, children, lateral, rodape, chaveEntrada, chaveTroca, ocupado = false }: Props) {
  const raiz = useRef<HTMLDivElement>(null);
  const linha = useRef<gsap.core.Timeline | null>(null);
  const anterior = useRef<{ entrada: unknown; troca: unknown }>({ entrada: undefined, troca: undefined });

  useGSAP(
    () => {
      const el = raiz.current;
      if (!el || chaveEntrada === undefined) return;
      const q = gsap.utils.selector(el);
      // É troca só quando a resposta é a mesma e o prato mudou; qualquer outra coisa
      // (inclusive a remontagem dupla do StrictMode) é uma entrada completa.
      const novaEntrada = !(anterior.current.entrada === chaveEntrada && anterior.current.troca !== chaveTroca);
      anterior.current = { entrada: chaveEntrada, troca: chaveTroca };

      const topoEl = q("[data-entrada=topo]");
      const pratoEl = q("[data-entrada=prato]");
      const cartao = q("[data-entrada=cartao]");

      comMovimento(
        el,
        () => {
          // Ao terminar (ou ser completada na marra), não sobra estilo inline: o CSS volta a mandar.
          const tl = gsap.timeline({
            defaults: { ease: EASE_SUAVE },
            onComplete: () => {
              gsap.set(tl.getChildren(false, true, false).flatMap((t) => t.targets()), {
                clearProps: "transform,opacity",
              });
            },
          });
          linha.current = tl;
          if (!novaEntrada) {
            // Troca de alternativa: o prato novo gira um pouco até assentar, o texto se acomoda.
            tl.from(pratoEl, { rotation: -20, scale: 0.97, duration: 0.6, ease: EASE_CHEGADA }, 0)
              .from(topoEl, { y: 6, opacity: 0.35, duration: 0.35 }, 0)
              .from(cartao, { y: 8, opacity: 0.4, duration: 0.35 }, 0.03);
            return;
          }
          const etiquetas = q("[data-entrada=cartao] [data-entrada=etiqueta]");
          const itens = q("[data-entrada=item]");
          const lateralEl = itens.length ? [] : q("[data-entrada=lateral]");
          const rodapeEl = q("[data-entrada=rodape]");

          // Total ≤ 0,9 s; título e cartão legíveis antes de 0,4 s.
          tl.from(topoEl, { y: 18, opacity: 0, duration: 0.5 }, 0)
            .from(pratoEl, { rotation: -32, scale: 0.94, duration: 0.9, ease: EASE_CHEGADA }, 0)
            .from(pratoEl, { opacity: 0, duration: 0.25, ease: "power1.out" }, 0)
            .from(cartao, { y: 28, duration: 0.6 }, 0.06)
            .from(cartao, { opacity: 0, duration: 0.3, ease: "power1.out" }, 0.06);
          if (etiquetas.length) {
            tl.from(
              etiquetas,
              { scale: 0.8, opacity: 0, duration: 0.35, ease: "back.out(2.2)", stagger: 0.05 },
              0.3,
            );
          }
          if (itens.length) tl.from(itens, { y: 16, opacity: 0, duration: 0.45, stagger: 0.08 }, 0.22);
          if (lateralEl.length) tl.from(lateralEl, { y: 16, opacity: 0, duration: 0.45 }, 0.22);
          if (rodapeEl.length) tl.from(rodapeEl, { y: 14, opacity: 0, duration: 0.45 }, 0.3);
        },
        () => {
          // Menos movimento: no máximo um fade curto do cartão, só quando a tela é nova.
          if (novaEntrada && cartao.length) {
            linha.current = gsap.timeline().from(cartao, { opacity: 0, duration: 0.12, ease: "none" });
          }
        },
      );
    },
    { scope: raiz, dependencies: [chaveEntrada, chaveTroca], revertOnUpdate: true },
  );

  // Pedido novo no meio da entrada: termina a coreografia na hora, sem deixar nada pela metade.
  useEffect(() => {
    if (ocupado) linha.current?.progress(1);
  }, [ocupado]);

  return (
    <div ref={raiz} className="flex flex-1 flex-col">
      <header className="cozinha relative">
        <div className="relative mx-auto min-h-[19.5rem] w-full max-w-6xl px-4 pb-24 pt-5 sm:px-8 md:min-h-[27rem] md:pb-36 md:pt-8">
          <p translate="no" className="flex items-center gap-2.5 font-titulo text-[1.0625rem] font-semibold tracking-[-0.01em] text-creme-quente">
            <span aria-hidden="true" className="prato prato-pequeno prato-caldo size-6" />
            Sugestão da Casa
          </p>
          <div
            data-entrada="topo"
            className="relative z-10 mt-8 max-w-[60%] sm:max-w-[62%] md:mt-14 md:max-w-[34rem] lg:max-w-[38rem]"
          >
            {topo}
          </div>
          <div className="pointer-events-none absolute right-[-1.75rem] top-[4.75rem] size-[9.75rem] sm:right-4 sm:size-[13rem] md:right-8 md:top-auto md:-bottom-28 md:size-[21rem] lg:right-10 lg:size-[23rem]">
            <div data-entrada="prato" className="size-full">
              {prato}
            </div>
            {ocupado ? <Vapor /> : null}
          </div>
        </div>
      </header>

      <div className="relative mx-auto -mt-16 grid w-full max-w-6xl flex-1 grid-cols-1 gap-y-10 px-4 pb-16 sm:px-8 md:-mt-24 md:grid-cols-12 md:content-start md:gap-x-12 md:pb-24">
        <div data-entrada="cartao" className="md:col-span-7 md:col-start-1 md:row-start-1">
          {children}
        </div>
        {lateral ? (
          <div
            data-entrada="lateral"
            className="md:col-span-5 md:col-start-8 md:row-span-2 md:row-start-1 md:pt-[14.5rem] lg:pt-[16rem]"
          >
            {lateral}
          </div>
        ) : null}
        {rodape ? (
          <div data-entrada="rodape" className="md:col-span-7 md:col-start-1 md:row-start-2">
            {rodape}
          </div>
        ) : null}
      </div>
    </div>
  );
}
