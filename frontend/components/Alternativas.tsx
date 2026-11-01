import { useId } from "react";
import { formatarReais } from "@/lib/formato";
import type { PratoSugerido } from "@/lib/tipos";
import { FotoPrato } from "./FotoPrato";

interface Props {
  pratos: PratoSugerido[];
  /** Id do prato que a casa escolheu primeiro, para identificá-lo se ele virar alternativa. */
  escolhaDaCasaId: string | null;
  aoEscolher: (prato: PratoSugerido) => void;
}

/** "Ou, se preferir": duas opções compactas que dizem no que diferem. Tocar troca a principal. */
export function Alternativas({ pratos, escolhaDaCasaId, aoEscolher }: Props) {
  const tituloId = useId();
  if (pratos.length === 0) return null;
  return (
    <section>
      <h2 id={tituloId} className="font-titulo text-[1.125rem] italic text-texto-suave">
        Ou, se preferir
      </h2>
      <ul aria-labelledby={tituloId} className="mt-3 flex flex-col gap-1">
        {pratos.map((p) => {
          const diferenca = p.diferenca ?? (p.id === escolhaDaCasaId ? "a escolha da casa" : null);
          return (
            <li key={p.id}>
              <button
                type="button"
                onClick={() => aoEscolher(p)}
                className="group -mx-3 flex min-h-16 w-[calc(100%+1.5rem)] items-center gap-4 rounded-2xl px-3 py-2.5 text-left transition-colors duration-200 hover:bg-cartao"
              >
                <FotoPrato nome={p.nome} fotoUrl={p.foto_url} tamanho="pequeno" sizes="56px" className="size-14" />
                <span className="min-w-0 flex-1">
                  <span className="block font-titulo text-[1.0625rem] font-semibold leading-snug text-tinta">
                    {p.nome}
                  </span>
                  <span className="mt-0.5 block text-[0.8125rem] text-texto-suave">
                    {diferenca ? `${diferenca} · ` : ""}
                    <span className="numeros">{p.tempo_min} min</span>
                  </span>
                </span>
                <span className="numeros flex-none font-titulo text-[1.0625rem] font-semibold text-tomate">
                  {formatarReais(p.total_centavos)}
                </span>
                <span className="sr-only">, trocar para este</span>
                <svg
                  viewBox="0 0 20 20"
                  aria-hidden="true"
                  className="size-4 flex-none text-texto-suave transition-[translate,color] duration-200 ease-saida group-hover:-translate-y-0.5 group-hover:text-tomate"
                >
                  <path
                    d="M10 15.5V4.5M5.5 9 10 4.5 14.5 9"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.9"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </button>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
