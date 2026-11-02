"use client";

import { useEffect, useState } from "react";

export const MENSAGENS_PENSANDO = [
  "Lendo sua vontade…",
  "Perguntando à cozinha…",
  "Conferindo o cardápio…",
  "Escolhendo o prato…",
] as const;

const INTERVALO_MS = 1900;

interface Props {
  /** O pedido que está sendo lido, mostrado entre aspas. */
  frase?: string | null;
  /** Versão de uma linha, para o campo de ajuste. */
  compacto?: boolean;
}

/** Estado de espera: mensagens curtas que se alternam, no mesmo quadro do envio. */
export function Pensando({ frase, compacto = false }: Props) {
  const [i, setI] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setI((n) => (n + 1) % MENSAGENS_PENSANDO.length), INTERVALO_MS);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="flex h-full flex-col justify-center gap-3">
      <div className="flex items-center gap-3">
        <span aria-hidden="true" className="flex gap-1.5">
          {[0, 1, 2].map((n) => (
            <span
              key={n}
              className="respirando size-2 rounded-full bg-tomate"
              style={{ animationDelay: `${n * 0.18}s` }}
            />
          ))}
        </span>
        <p
          className={`font-titulo italic leading-tight text-tinta ${compacto ? "text-[1.0625rem]" : "text-[1.375rem]"}`}
        >
          {MENSAGENS_PENSANDO[i]}
        </p>
      </div>
      {frase && !compacto ? (
        <p className="line-clamp-2 max-w-[52ch] text-[0.9375rem] leading-relaxed text-texto-suave">“{frase}”</p>
      ) : null}
    </div>
  );
}
