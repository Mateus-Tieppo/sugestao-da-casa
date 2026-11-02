import type { TipoFalha } from "@/lib/api";
import { Cozinha } from "./Cozinha";
import { CLASSE_BOTAO_PRIMARIO, CLASSE_BOTAO_SECUNDARIO, CLASSE_CARTAO } from "./estilos";
import { PratoVazio } from "./PratoVazio";
import { TituloTela } from "./TituloTela";

const EXPLICACAO: Record<TipoFalha, { topo: string; corpo: string }> = {
  timeout: {
    topo: "Às vezes ela demora para acordar.",
    corpo: "A cozinha demorou mais do que devia. Costuma funcionar na segunda vez.",
  },
  rede: {
    topo: "Parece que a conexão caiu.",
    corpo: "Sem conexão com a cozinha agora. Confira a internet e tente de novo.",
  },
  servidor: {
    topo: "Deu um problema do lado de lá.",
    corpo: "A cozinha tropeçou no meio do pedido. Não foi nada do que você escreveu.",
  },
};

interface Props {
  erro: TipoFalha;
  tentarDeNovo: () => void;
  /** Volta ao início para escrever outro pedido. */
  aoRecomecar?: () => void;
}

/** A API não respondeu: o mesmo desenho das outras telas, com uma saída clara. */
export function FalhaAmigavel({ erro, tentarDeNovo, aoRecomecar }: Props) {
  const texto = EXPLICACAO[erro];
  return (
    <Cozinha chaveEntrada={erro} topo={<TituloTela titulo="A cozinha não respondeu." texto={texto.topo} />} prato={<PratoVazio talheres />}>
      <section aria-labelledby="falha-titulo" className={CLASSE_CARTAO}>
        <h2
          id="falha-titulo"
          className="font-titulo text-[1.375rem] font-normal leading-snug tracking-[-0.01em] text-tinta text-balance sm:text-[1.625rem]"
        >
          {texto.corpo}
        </h2>
        <p className="mt-3 text-[0.9375rem] leading-relaxed text-[#4a362a]">Nada se perdeu: o seu pedido continua aqui.</p>
        <button type="button" onClick={tentarDeNovo} className={`${CLASSE_BOTAO_PRIMARIO} mt-6`}>
          Tentar de novo
        </button>
        {aoRecomecar ? (
          <button type="button" onClick={aoRecomecar} className={`${CLASSE_BOTAO_SECUNDARIO} mt-2`}>
            Escrever outro pedido
          </button>
        ) : null}
      </section>
    </Cozinha>
  );
}
