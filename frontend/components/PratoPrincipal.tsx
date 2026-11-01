import { useId } from "react";
import { formatarReais } from "@/lib/formato";
import type { PratoSugerido } from "@/lib/tipos";

/** O botão que abre o pedido; ao fechar o carrinho o foco volta para ele. */
export const ID_QUERO_ESSE = "quero-esse";

const TEMPO = /^\d+\s*min$/;

interface Props {
  prato: PratoSugerido;
  aoQuerer: (prato: PratoSugerido) => void;
  /** Esmaece o conteúdo (não o cartão) enquanto a cozinha refaz a sugestão. */
  esmaecido?: boolean;
}

/** Cartão creme da sugestão: nome, preço com entrega, o porquê, etiquetas e o botão de pedir. */
export function PratoPrincipal({ prato, aoQuerer, esmaecido = false }: Props) {
  const tituloId = useId();
  return (
    <article
      aria-labelledby={tituloId}
      aria-busy={esmaecido || undefined}
      className="rounded-2xl bg-cartao p-5 shadow-[0_22px_44px_-18px_rgb(90_30_10/0.35),0_3px_8px_rgb(90_30_10/0.08)] sm:p-7"
    >
      <div className={`transition-opacity duration-300 ease-saida ${esmaecido ? "opacity-45" : ""}`}>
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <h2
              id={tituloId}
              className="font-titulo text-[1.375rem] font-semibold leading-tight tracking-[-0.01em] text-tinta sm:text-[1.625rem] text-balance"
            >
              {prato.nome}
            </h2>
            <p className="mt-1 text-[0.875rem] text-texto-suave">{prato.restaurante}</p>
          </div>
          <div className="flex-none text-right">
            <p className="numeros font-titulo text-[1.375rem] font-semibold leading-tight text-tomate sm:text-[1.625rem]">
              {formatarReais(prato.total_centavos)}
            </p>
            <p className="mt-1 text-[0.75rem] text-texto-suave">com entrega</p>
          </div>
        </div>

        <p className="mt-4 max-w-[60ch] text-[0.9375rem] leading-relaxed text-[#4a362a]">{prato.explicacao}</p>

        {prato.etiquetas.length > 0 ? (
          <ul aria-label="Detalhes do prato" className="mt-4 flex flex-wrap gap-1.5">
            {prato.etiquetas.map((e) => (
              <li
                key={e}
                className={`rounded-full px-2.5 py-1 text-[0.75rem] font-semibold ${
                  TEMPO.test(e) ? "numeros bg-acafrao-claro text-acafrao-escuro" : "bg-manjericao-claro text-manjericao"
                }`}
              >
                {e}
              </li>
            ))}
          </ul>
        ) : null}

        <button
          id={ID_QUERO_ESSE}
          type="button"
          onClick={() => aoQuerer(prato)}
          className="mt-6 flex h-[3.25rem] w-full items-center justify-center rounded-xl bg-tomate text-[1rem] font-semibold text-[#fff8ec] shadow-[0_10px_22px_-8px_rgb(200_51_27/0.6)] transition-[background-color,translate] duration-200 ease-saida hover:bg-tomate-escuro active:translate-y-px"
        >
          Quero esse
        </button>
      </div>
    </article>
  );
}
