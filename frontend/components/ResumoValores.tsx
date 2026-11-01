import { entregaCarrinho, subtotalCarrinho, totalCarrinho, type EstadoCarrinho } from "@/lib/carrinho";
import { formatarReais } from "@/lib/formato";

/** Pratos, entrega e total, na mesma forma no carrinho e na confirmação. */
export function ResumoValores({ estado }: { estado: EstadoCarrinho }) {
  return (
    <dl className="space-y-2 text-[0.9375rem]">
      <div className="flex justify-between gap-4">
        <dt className="text-texto-suave">Pratos</dt>
        <dd className="numeros text-tinta">{formatarReais(subtotalCarrinho(estado))}</dd>
      </div>
      <div className="flex justify-between gap-4">
        <dt className="text-texto-suave">Entrega</dt>
        <dd className="numeros text-tinta">{formatarReais(entregaCarrinho(estado))}</dd>
      </div>
      <div className="flex items-baseline justify-between gap-4 border-t border-borda pt-3">
        <dt className="font-semibold text-tinta">Total</dt>
        <dd data-testid="total" className="numeros font-titulo text-[1.5rem] font-semibold leading-none text-tomate">
          {formatarReais(totalCarrinho(estado))}
        </dd>
      </div>
    </dl>
  );
}
