"use client";

import { useId, useState, type FormEvent } from "react";
import { LIMITES, type Etiqueta } from "@/lib/tipos";
import { Entendido } from "./Entendido";
import { Pensando } from "./Pensando";

interface Props {
  etiquetas: Etiqueta[];
  aoRemover: (chave: string) => void;
  aoEnviar: (texto: string) => void;
  pensando: boolean;
  frasePensando?: string | null;
}

/** "Quer ajustar?": o que foi entendido, removível, e um campo para refinar em texto. */
export function Ajuste({ etiquetas, aoRemover, aoEnviar, pensando, frasePensando }: Props) {
  const [texto, setTexto] = useState("");
  const campoId = useId();
  const vazio = texto.trim().length === 0;

  function aoSubmeter(e: FormEvent) {
    e.preventDefault();
    if (vazio || pensando) return;
    aoEnviar(texto);
    setTexto("");
  }

  return (
    <section className="border-t border-borda pt-8">
      <h2 className="font-titulo text-[1.375rem] font-semibold tracking-[-0.01em] text-tinta">
        <label htmlFor={campoId}>Quer ajustar?</label>
      </h2>
      <div className="mt-4">
        <Entendido etiquetas={etiquetas} aoRemover={aoRemover} desabilitado={pensando} />
      </div>
      <div className="mt-5 min-h-[3.5rem]">
        {pensando ? (
          <div className="flex min-h-[3.5rem] items-center rounded-xl bg-cartao px-4 py-2">
            <Pensando frase={frasePensando} compacto />
          </div>
        ) : (
          <form
            onSubmit={aoSubmeter}
            className="flex min-h-[3.5rem] items-center gap-2 rounded-xl border border-borda bg-cartao py-1.5 pl-4 pr-1.5 transition-shadow duration-200 has-[input:focus]:border-tomate/50 has-[input:focus]:ring-2 has-[input:focus]:ring-tomate/25"
          >
            <input
              id={campoId}
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              maxLength={LIMITES.texto}
              placeholder="mais barato, sem cebola, algo mais leve..."
              autoComplete="off"
              enterKeyHint="send"
              className="min-w-0 flex-1 bg-transparent text-[1rem] text-tinta placeholder:text-texto-suave focus:outline-none"
            />
            <button
              type="submit"
              disabled={vazio}
              className="h-11 flex-none rounded-lg bg-tinta px-4 text-[0.9375rem] font-semibold text-creme-quente transition-colors duration-200 hover:bg-[#3d2a1f] disabled:cursor-not-allowed disabled:bg-[#e3cdb4] disabled:text-texto-suave"
            >
              Ajustar
            </button>
          </form>
        )}
      </div>
    </section>
  );
}
