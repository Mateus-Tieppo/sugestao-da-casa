"use client";

import { useId, useState, type FormEvent, type KeyboardEvent } from "react";
import { LIMITES } from "@/lib/tipos";
import { ID_CAMPO_PEDIDO } from "./Cozinha";
import { Pensando } from "./Pensando";

export const EXEMPLOS = [
  "algo quentinho, não muito pesado, até R$ 40, sem lactose",
  "quero algo fresquinho e rápido, sem glúten",
] as const;

const AVISO_CONTADOR = LIMITES.texto - 60;

interface Props {
  aoEnviar: (texto: string) => void;
  pensando: boolean;
  /** Pedido em andamento, mostrado enquanto a cozinha pensa. */
  frasePensando?: string | null;
}

/** Quadro do pedido: o campo grande, o botão e os exemplos. Vira o "pensando" no mesmo lugar. */
export function Compositor({ aoEnviar, pensando, frasePensando }: Props) {
  const [texto, setTexto] = useState("");
  const campoId = ID_CAMPO_PEDIDO;
  const contadorId = useId();
  const vazio = texto.trim().length === 0;

  function enviar(frase: string) {
    if (!frase.trim() || pensando) return;
    aoEnviar(frase);
  }

  function aoSubmeter(e: FormEvent) {
    e.preventDefault();
    enviar(texto);
  }

  function aoTeclar(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      enviar(texto);
    }
  }

  return (
    <div>
      <div className="relative min-h-[13.5rem] rounded-2xl bg-cartao transition-shadow duration-200 has-[textarea:focus-visible]:ring-[3px] has-[textarea:focus-visible]:ring-tomate shadow-[0_18px_40px_-12px_rgb(90_30_10/0.28),0_2px_6px_rgb(90_30_10/0.08)]">
        {pensando ? (
          <div className="absolute inset-0 px-5 py-5 sm:px-7">
            <Pensando frase={frasePensando} />
          </div>
        ) : (
          <form onSubmit={aoSubmeter} className="flex min-h-[13.5rem] flex-col px-5 pb-4 pt-5 sm:px-7 sm:pt-6">
            <label htmlFor={campoId} className="font-titulo text-[1.125rem] text-tinta">
              O que você quer comer?
            </label>
            <textarea
              id={campoId}
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              onKeyDown={aoTeclar}
              maxLength={LIMITES.texto}
              rows={3}
              placeholder="Conta do seu jeito: fome, bolso, pressa, o que não pode..."
              aria-describedby={texto.length >= AVISO_CONTADOR ? contadorId : undefined}
              className="mt-2 w-full flex-1 resize-none bg-transparent text-[1.0625rem] leading-relaxed text-tinta placeholder:text-texto-suave focus:outline-none"
            />
            <div className="mt-3 flex items-center justify-end gap-4">
              {texto.length >= AVISO_CONTADOR ? (
                <span
                  id={contadorId}
                  className={`numeros text-[0.8125rem] ${texto.length >= LIMITES.texto ? "font-semibold text-tomate-escuro" : "text-texto-suave"}`}
                >
                  {texto.length}/{LIMITES.texto}
                </span>
              ) : null}
              <button
                type="submit"
                disabled={vazio}
                className="inline-flex h-12 items-center gap-2 rounded-xl bg-tomate px-5 font-semibold text-[#fff8ec] shadow-[0_8px_18px_-6px_rgb(200_51_27/0.55)] transition-[background-color,box-shadow,translate] duration-200 ease-saida hover:bg-tomate-escuro active:translate-y-px disabled:cursor-not-allowed disabled:bg-[#e3cdb4] disabled:text-texto-suave disabled:shadow-none"
              >
                Pedir sugestão
                <svg viewBox="0 0 20 20" aria-hidden="true" className="size-4">
                  <path
                    d="M4 10h11m-4-4.5L15.5 10 11 14.5"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.9"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </button>
            </div>
          </form>
        )}
      </div>

      <div className={pensando ? "invisible" : undefined} aria-hidden={pensando || undefined}>
        <p className="mt-7 text-[0.8125rem] font-medium text-texto-suave">Ou comece por um destes</p>
        <ul className="mt-2.5 flex flex-col gap-2.5 sm:flex-row">
          {EXEMPLOS.map((exemplo) => (
            <li key={exemplo} className="sm:flex-1">
              <button
                type="button"
                onClick={() => enviar(exemplo)}
                tabIndex={pensando ? -1 : undefined}
                className="group flex min-h-12 w-full items-center justify-between gap-3 rounded-xl border border-borda bg-transparent px-4 py-3 text-left font-titulo text-[1.0625rem] italic leading-snug text-tinta transition-colors duration-200 hover:border-tomate/40 hover:bg-cartao"
              >
                <span>{exemplo}</span>
                <svg
                  viewBox="0 0 20 20"
                  aria-hidden="true"
                  className="size-4 flex-none text-tomate transition-transform duration-200 ease-saida group-hover:translate-x-0.5"
                >
                  <path
                    d="M4 10h11m-4-4.5L15.5 10 11 14.5"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.9"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
