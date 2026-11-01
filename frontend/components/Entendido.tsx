import { useId } from "react";
import type { Etiqueta } from "@/lib/tipos";

interface Props {
  etiquetas: Etiqueta[];
  aoRemover: (chave: string) => void;
  desabilitado?: boolean;
}

/** O que a casa entendeu do pedido, com um botão para tirar cada item. */
export function Entendido({ etiquetas, aoRemover, desabilitado = false }: Props) {
  const tituloId = useId();
  if (etiquetas.length === 0) return null;
  return (
    <div>
      <p id={tituloId} className="text-[0.8125rem] font-medium text-texto-suave">
        O que eu entendi
      </p>
      <ul aria-labelledby={tituloId} className="mt-2 flex flex-wrap gap-2">
        {etiquetas.map((e) => (
          <li
            key={e.chave}
            className="flex items-center rounded-full border border-borda bg-cartao py-1 pl-3.5 pr-1 text-sm font-medium text-tinta"
          >
            {e.rotulo}
            <button
              type="button"
              onClick={() => aoRemover(e.chave)}
              disabled={desabilitado}
              aria-label={`Remover ${e.rotulo}`}
              className="relative ml-1 grid size-7 place-items-center rounded-full text-texto-suave transition-colors duration-150 before:absolute before:-inset-2 before:content-[''] hover:bg-acafrao-claro hover:text-tomate-escuro disabled:opacity-40"
            >
              <svg viewBox="0 0 16 16" aria-hidden="true" className="size-3.5">
                <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
              </svg>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
