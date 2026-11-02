"use client";

import { useRef } from "react";
import { comMovimento, gsap, useGSAP } from "@/lib/movimento";

const FIOS = [
  "M38 92c-7-10 6-18 0-30s7-20 2-32",
  "M52 96c-6-12 7-20 1-33s6-20 1-35",
  "M66 92c-7-10 6-17 0-29s6-19 2-31",
];

/**
 * Vapor sutil saindo do prato enquanto a cozinha pensa. Decorativo: começa invisível
 * e só aparece animado; com menos movimento (ou sem script) simplesmente não aparece.
 */
export function Vapor() {
  const raiz = useRef<SVGSVGElement>(null);

  useGSAP(
    () => {
      comMovimento(
        raiz.current,
        () => {
          gsap.set("path", { y: 14, scaleY: 0.8, transformOrigin: "50% 100%" });
          gsap.to("path", {
            keyframes: { y: [0, -26], opacity: [0.5, 0], scaleY: [1, 1.12], easeEach: "sine.inOut" },
            x: "random(-3, 3)",
            duration: 2.6,
            ease: "none",
            stagger: { each: 0.75, repeat: -1 },
          });
        },
        () => {},
      );
    },
    { scope: raiz },
  );

  return (
    <svg
      ref={raiz}
      aria-hidden="true"
      viewBox="0 0 100 100"
      className="pointer-events-none absolute left-1/2 top-[-26%] z-10 h-[74%] w-[56%] blur-[1.5px] -translate-x-1/2 overflow-visible"
    >
      {FIOS.map((d) => (
        <path
          key={d}
          d={d}
          fill="none"
          stroke="#fff4e2"
          strokeWidth="6"
          strokeLinecap="round"
          style={{ opacity: 0 }}
        />
      ))}
    </svg>
  );
}
