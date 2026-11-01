import type { ReactNode } from "react";

/** O h1 de cada tela recebe o foco quando a tela muda (teclado e leitor de tela). */
export const ID_TITULO = "titulo-tela";
/** O campo principal do pedido, focado ao voltar para o início. */
export const ID_CAMPO_PEDIDO = "campo-pedido";

interface Props {
  /** O h1 e o que vem logo abaixo dele, dentro do bloco quente. */
  topo: ReactNode;
  /** O prato em destaque, à direita do bloco quente. */
  prato: ReactNode;
  /** Coluna principal: começa sobreposta à borda do bloco quente. */
  children: ReactNode;
  /** Coluna lateral no desktop, embaixo do prato; no celular vem depois da principal. */
  lateral?: ReactNode;
  /** Embaixo da coluna principal no desktop; no celular vem por último. */
  rodape?: ReactNode;
}

/**
 * A "cozinha aberta": bloco páprica no topo, prato em destaque e um cartão creme
 * que sobe por cima da borda. Início e resultado usam o mesmo esqueleto,
 * então a troca de tela não muda o desenho da página.
 */
export function Cozinha({ topo, prato, children, lateral, rodape }: Props) {
  return (
    <div className="flex flex-1 flex-col">
      <header className="cozinha relative">
        <div className="relative mx-auto min-h-[19.5rem] w-full max-w-6xl px-4 pb-24 pt-5 sm:px-8 md:min-h-[27rem] md:pb-36 md:pt-8">
          <p className="flex items-center gap-2.5 font-titulo text-[1.0625rem] font-semibold tracking-[-0.01em] text-creme-quente">
            <span aria-hidden="true" className="prato prato-pequeno prato-caldo size-6" />
            Sugestão da Casa
          </p>
          <div className="relative z-10 mt-8 max-w-[60%] sm:max-w-[62%] md:mt-14 md:max-w-[34rem] lg:max-w-[38rem]">
            {topo}
          </div>
          <div className="pointer-events-none absolute right-[-1.75rem] top-[4.75rem] size-[9.75rem] sm:right-4 sm:size-[13rem] md:right-8 md:top-auto md:-bottom-28 md:size-[21rem] lg:right-10 lg:size-[23rem]">
            {prato}
          </div>
        </div>
      </header>

      <div className="relative mx-auto -mt-16 grid w-full max-w-6xl flex-1 grid-cols-1 gap-y-10 px-4 pb-16 sm:px-8 md:-mt-24 md:grid-cols-12 md:content-start md:gap-x-12 md:pb-24">
        <div className="md:col-span-7 md:col-start-1 md:row-start-1">{children}</div>
        {lateral ? (
          <div className="md:col-span-5 md:col-start-8 md:row-span-2 md:row-start-1 md:pt-[14.5rem] lg:pt-[16rem]">
            {lateral}
          </div>
        ) : null}
        {rodape ? <div className="md:col-span-7 md:col-start-1 md:row-start-2">{rodape}</div> : null}
      </div>
    </div>
  );
}
