import type { RespostaSugestao } from "@/lib/tipos";

/** Aviso discreto de que a resposta veio do modo demonstração, sem a IA. */
export function SeloDemonstracao({ modo }: { modo: RespostaSugestao["modo"] }) {
  if (modo !== "demonstracao") return null;
  return (
    <p className="flex items-start gap-2.5 text-[0.8125rem] leading-snug text-texto-suave">
      <span
        aria-hidden="true"
        className="mt-[0.4em] size-2 flex-none rounded-full bg-acafrao ring-4 ring-acafrao-claro"
      />
      Modo demonstração: respostas mais simples enquanto a IA descansa.
    </p>
  );
}
