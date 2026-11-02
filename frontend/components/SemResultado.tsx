import { formatarReais } from "@/lib/formato";
import type { MudancaSugerida, RespostaSugestao } from "@/lib/tipos";
import { Ajuste } from "./Ajuste";
import { Cozinha } from "./Cozinha";
import { CLASSE_BOTAO_PRIMARIO, CLASSE_CARTAO } from "./estilos";
import { FotoPrato } from "./FotoPrato";
import { PratoVazio } from "./PratoVazio";
import { TituloTela } from "./TituloTela";

/** "Subir para R$ 19 e esperar 15 min": o botão diz tudo o que vai mudar. */
export function rotuloDaProposta(mudancas: MudancaSugerida[]): string {
  const orcamento = mudancas.find((m) => m.campo === "orcamento");
  const tempo = mudancas.find((m) => m.campo === "tempo");
  if (orcamento && tempo) {
    return `Subir para ${formatarReais(orcamento.valor_sugerido)} e esperar ${tempo.valor_sugerido} min`;
  }
  if (orcamento) return `Subir para ${formatarReais(orcamento.valor_sugerido)}`;
  if (tempo) return `Esperar até ${tempo.valor_sugerido} min`;
  return "Aceitar a mudança";
}

interface Props {
  resposta: RespostaSugestao;
  aoAceitar: () => void;
  aoRemover: (chave: string) => void;
  aoEnviar: (texto: string) => void;
  pensando: boolean;
  frasePensando?: string | null;
}

/** Nada passou por todas as exigências: a casa propõe o menor passo, ou pede para afrouxar a frase. */
export function SemResultado({ resposta, aoAceitar, aoRemover, aoEnviar, pensando, frasePensando }: Props) {
  const proposta = resposta.proposta;
  const prato = proposta?.prato;

  return (
    <Cozinha
      chaveEntrada={resposta}
      ocupado={pensando}
      topo={
        <TituloTela
          titulo="Com tudo isso junto, não achei."
          texto={proposta ? "Mas dá para chegar perto." : "O cardápio de hoje não fecha com tantas exigências."}
        />
      }
      prato={<PratoVazio />}
      lateral={
        <Ajuste
          etiquetas={resposta.entendido}
          aoRemover={aoRemover}
          aoEnviar={aoEnviar}
          pensando={pensando}
          frasePensando={frasePensando}
        />
      }
    >
      {proposta && prato ? (
        <section aria-labelledby="proposta-titulo" className={CLASSE_CARTAO}>
          <div aria-busy={pensando || undefined} className={`transition-opacity duration-300 ease-saida ${pensando ? "opacity-45" : ""}`}>
            <h2
              id="proposta-titulo"
              className="font-titulo text-[1.375rem] font-normal leading-snug tracking-[-0.01em] text-tinta text-balance sm:text-[1.625rem]"
            >
              {proposta.mensagem}
            </h2>

            <div className="mt-5 flex items-center gap-4 rounded-xl bg-papel p-3 pr-4">
              <FotoPrato
                nome={prato.nome}
                fotoUrl={prato.foto_url}
                tamanho="medio"
                sizes="64px"
                className="size-16 flex-none"
              />
              <div className="min-w-0 flex-1">
                <p className="font-titulo text-[1.0625rem] font-semibold leading-tight text-tinta">{prato.nome}</p>
                <p className="mt-0.5 text-[0.8125rem] text-texto-suave">{prato.restaurante}</p>
                <p className="numeros text-[0.8125rem] text-texto-suave">{prato.tempo_min} min</p>
              </div>
              <div className="flex-none text-right">
                <p className="numeros font-titulo text-[1.25rem] font-semibold leading-tight text-tomate">
                  {formatarReais(prato.total_centavos)}
                </p>
                <p className="text-[0.75rem] text-texto-suave">com entrega</p>
              </div>
            </div>

            <button type="button" onClick={aoAceitar} disabled={pensando} className={`${CLASSE_BOTAO_PRIMARIO} mt-5 disabled:opacity-60`}>
              {rotuloDaProposta(proposta.mudancas)}
            </button>
            <p className="mt-3 text-center text-[0.8125rem] text-texto-suave">
              Ou ajuste o pedido do seu jeito.
            </p>
          </div>
        </section>
      ) : (
        <section aria-labelledby="sem-proposta-titulo" className={CLASSE_CARTAO}>
          <h2
            id="sem-proposta-titulo"
            className="font-titulo text-[1.375rem] font-normal leading-snug tracking-[-0.01em] text-tinta text-balance sm:text-[1.625rem]"
          >
            Nenhum prato passa por todas as exigências ao mesmo tempo.
          </h2>
          <p className="mt-3 max-w-[48ch] text-[0.9375rem] leading-relaxed text-[#4a362a]">
            Tire alguma exigência ou escreva de outro jeito. Com uma a menos, a casa costuma achar o que servir.
          </p>
        </section>
      )}
    </Cozinha>
  );
}
