import { tempoEstimadoMin, type EstadoCarrinho } from "@/lib/carrinho";
import { formatarReais } from "@/lib/formato";
import { Cozinha } from "./Cozinha";
import { CLASSE_BOTAO_PRIMARIO, CLASSE_CARTAO } from "./estilos";
import { FotoPrato } from "./FotoPrato";
import { ResumoValores } from "./ResumoValores";
import { TituloTela } from "./TituloTela";

interface Props {
  estado: EstadoCarrinho;
  aoReiniciar: () => void;
}

/** Pedido simulado: fecha a história com o prato escolhido e deixa claro que nada foi cobrado. */
export function Confirmacao({ estado, aoReiniciar }: Props) {
  const primeiro = estado.itens[0]?.prato;
  return (
    <Cozinha
      topo={
        <TituloTela
          titulo={
            <>
              Pedido feito. <em className="text-acafrao">Bom apetite!</em>
            </>
          }
          texto={`Previsão de chegada: cerca de ${tempoEstimadoMin(estado)} min.`}
        />
      }
      prato={
        primeiro ? (
          <FotoPrato
            nome={primeiro.nome}
            fotoUrl={primeiro.foto_url}
            tamanho="grande"
            sizes="(min-width: 1024px) 368px, (min-width: 768px) 336px, (min-width: 640px) 208px, 156px"
            className="size-full"
          />
        ) : (
          <div className="prato prato-grande prato-caldo size-full" />
        )
      }
    >
      <section aria-labelledby="resumo-titulo" className={CLASSE_CARTAO}>
        <p className="rounded-xl bg-acafrao-claro px-4 py-3 text-[0.9375rem] font-semibold text-acafrao-escuro">
          Pedido simulado: nada foi cobrado
        </p>
        <h2 id="resumo-titulo" className="mt-6 font-titulo text-[1.375rem] font-semibold tracking-[-0.01em] text-tinta">
          Resumo do pedido
        </h2>
        <ul className="mt-3 divide-y divide-borda">
          {estado.itens.map(({ prato, quantidade }) => (
            <li key={prato.id} className="flex items-baseline justify-between gap-4 py-3">
              <div className="min-w-0">
                <p className="font-semibold text-tinta">
                  <span className="numeros">{quantidade}</span> × {prato.nome}
                </p>
                <p className="text-[0.8125rem] text-texto-suave">{prato.restaurante}</p>
              </div>
              <p className="numeros flex-none text-tinta">{formatarReais(prato.preco_centavos * quantidade)}</p>
            </li>
          ))}
        </ul>
        <div className="mt-3 border-t border-borda pt-4">
          <ResumoValores estado={estado} />
        </div>
        <button type="button" onClick={aoReiniciar} className={`${CLASSE_BOTAO_PRIMARIO} mt-6`}>
          Pedir outra coisa
        </button>
      </section>
    </Cozinha>
  );
}
