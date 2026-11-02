"use client";

import gsap from "gsap";
import { useGSAP } from "@gsap/react";

// Registro único: qualquer componente que anime importa daqui, nunca direto de "gsap".
gsap.registerPlugin(useGSAP);

export { gsap, useGSAP };

export const COM_MOVIMENTO = "(prefers-reduced-motion: no-preference)";
export const SEM_MOVIMENTO = "(prefers-reduced-motion: reduce)";

/** Curvas da casa: saída rápida e pouso macio, como o --ease-saida do CSS. */
export const EASE_CHEGADA = "expo.out";
export const EASE_SUAVE = "power3.out";

/**
 * Roda `animar` para quem não pediu menos movimento e `semMovimento` para quem pediu.
 * Usa gsap.matchMedia(): se a preferência mudar com a página aberta, o que foi criado
 * no ramo anterior é revertido e o outro ramo roda. Chamado dentro do useGSAP, a
 * limpeza acompanha o componente. Sem matchMedia (jsdom, navegador antigo) nada anima:
 * a página continua visível do jeito que o HTML chegou.
 */
export function comMovimento(
  contexto: Element | string | null | undefined,
  animar: () => void,
  semMovimento: () => void,
): gsap.MatchMedia | null {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") return null;
  const mm = gsap.matchMedia(contexto ?? undefined);
  mm.add({ animar: COM_MOVIMENTO, reduzir: SEM_MOVIMENTO }, (ctx) => {
    if (ctx.conditions?.reduzir) semMovimento();
    else if (ctx.conditions?.animar) animar();
  });
  return mm;
}
