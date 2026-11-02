"use client";

import { useEffect, useId, useRef } from "react";
import { QUANTIDADE_MAXIMA, QUANTIDADE_MINIMA, type EstadoCarrinho } from "@/lib/carrinho";
import { formatarReais } from "@/lib/formato";
import { CLASSE_BOTAO_PRIMARIO } from "./estilos";
import { FotoPrato } from "./FotoPrato";
import { ResumoValores } from "./ResumoValores";

interface Props {
  estado: EstadoCarrinho;
  aoAlterarQuantidade: (id: string, quantidade: number) => void;
  aoConfirmar: () => void;
  aoFechar: () => void;
}

const BOTAO_QUANTIDADE =
  "grid size-11 place-items-center rounded-full border border-borda bg-cartao text-tinta transition-colors duration-150 hover:bg-acafrao-claro disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-cartao";

/**
 * Carrinho como <dialog> modal nativo: o navegador prende o foco, fecha com Escape e deixa o resto inerte.
 * Painel inferior no celular, lateral no desktop. Quem abre decide devolver o foco ao botão de origem.
 */
export function Carrinho({ estado, aoAlterarQuantidade, aoConfirmar, aoFechar }: Props) {
  const ref = useRef<HTMLDialogElement>(null);
  const tituloId = useId();

  useEffect(() => {
    const dialogo = ref.current;
    if (dialogo && !dialogo.open) dialogo.showModal();
    // A página atrás não rola enquanto o pedido está aberto.
    const antes = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = antes;
    };
  }, []);

  return (
    <dialog
      ref={ref}
      aria-modal="true"
      aria-labelledby={tituloId}
      onCancel={(e) => {
        e.preventDefault();
        aoFechar();
      }}
      // O clique no fundo escurecido chega ao próprio <dialog>.
      onClick={(e) => {
        if (e.target === e.currentTarget) aoFechar();
      }}
      className="painel fixed overscroll-contain inset-x-0 bottom-0 top-auto m-0 max-h-[90dvh] w-full max-w-none overflow-hidden rounded-t-3xl bg-cartao p-0 text-tinta shadow-[0_-18px_48px_-12px_rgb(60_10_0/0.45)] backdrop:bg-[rgb(43_28_20/0.55)] open:flex open:flex-col md:inset-y-0 md:left-auto md:right-0 md:h-dvh md:max-h-none md:w-[28rem] md:rounded-l-3xl md:rounded-tr-none md:shadow-[-18px_0_48px_-12px_rgb(60_10_0/0.45)]"
    >
      <div className="flex items-center justify-between gap-4 px-5 pb-3 pt-5 sm:px-7">
        <h2 id={tituloId} className="font-titulo text-[1.625rem] font-semibold tracking-[-0.01em]">
          Seu pedido
        </h2>
        <button
          type="button"
          onClick={aoFechar}
          aria-label="Fechar o pedido"
          className="grid size-11 flex-none place-items-center rounded-full text-texto-suave transition-colors duration-150 hover:bg-acafrao-claro hover:text-tomate-escuro"
        >
          <svg viewBox="0 0 16 16" aria-hidden="true" className="size-4">
            <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
          </svg>
        </button>
      </div>

      <ul className="flex-1 divide-y divide-borda overflow-y-auto overscroll-contain px-5 sm:px-7">
        {estado.itens.map(({ prato, quantidade }) => (
          <li key={prato.id} className="py-4">
            <div className="flex items-center gap-4">
              <FotoPrato nome={prato.nome} fotoUrl={prato.foto_url} tamanho="medio" sizes="64px" className="size-16 flex-none" />
              <div className="min-w-0 flex-1">
                <p className="font-titulo text-[1.0625rem] font-semibold leading-tight">{prato.nome}</p>
                <p className="mt-0.5 text-[0.8125rem] text-texto-suave">{prato.restaurante}</p>
              </div>
              <p className="numeros flex-none font-titulo text-[1.0625rem] font-semibold">
                {formatarReais(prato.preco_centavos * quantidade)}
              </p>
            </div>
            <div role="group" aria-label={`Quantidade de ${prato.nome}`} className="mt-3 flex items-center justify-end gap-2">
              <button
                type="button"
                aria-label={`Diminuir quantidade de ${prato.nome}`}
                disabled={quantidade <= QUANTIDADE_MINIMA}
                onClick={() => aoAlterarQuantidade(prato.id, quantidade - 1)}
                className={BOTAO_QUANTIDADE}
              >
                <svg viewBox="0 0 16 16" aria-hidden="true" className="size-4">
                  <path d="M3.5 8h9" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
                </svg>
              </button>
              <span aria-live="polite" className="numeros w-8 text-center text-[1.0625rem] font-semibold">
                {quantidade}
              </span>
              <button
                type="button"
                aria-label={`Aumentar quantidade de ${prato.nome}`}
                disabled={quantidade >= QUANTIDADE_MAXIMA}
                onClick={() => aoAlterarQuantidade(prato.id, quantidade + 1)}
                className={BOTAO_QUANTIDADE}
              >
                <svg viewBox="0 0 16 16" aria-hidden="true" className="size-4">
                  <path d="M3.5 8h9M8 3.5v9" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
                </svg>
              </button>
            </div>
          </li>
        ))}
      </ul>

      <div className="border-t border-borda bg-papel px-5 pb-[max(1.25rem,env(safe-area-inset-bottom))] pt-5 sm:px-7">
        <ResumoValores estado={estado} />
        <button type="button" onClick={aoConfirmar} className={`${CLASSE_BOTAO_PRIMARIO} mt-5`}>
          Confirmar pedido
        </button>
        <p className="mt-3 text-center text-[0.8125rem] text-texto-suave">É uma demonstração: nada será cobrado de verdade.</p>
      </div>
    </dialog>
  );
}
