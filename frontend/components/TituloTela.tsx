import type { ReactNode } from "react";
import { ID_TITULO } from "./Cozinha";

interface Props {
  titulo: ReactNode;
  texto: string;
}

/** O h1 de uma tela simples (início, sem resultado, falha, confirmação) e a linha de apoio. */
export function TituloTela({ titulo, texto }: Props) {
  return (
    <>
      <h1
        id={ID_TITULO}
        tabIndex={-1}
        className="font-titulo text-[2.125rem] font-normal leading-[1.04] tracking-[-0.025em] text-balance outline-none sm:text-[2.75rem] md:text-[4rem]"
      >
        {titulo}
      </h1>
      <p className="mt-3 max-w-[38ch] text-[0.9375rem] leading-snug text-creme-rosado md:mt-5 md:text-[1.0625rem]">
        {texto}
      </p>
    </>
  );
}
