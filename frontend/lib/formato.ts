/** Formata centavos como reais: "R$ 32" (inteiro) ou "R$ 22,50", com espaço não separável. */
export function formatarReais(centavos: number): string {
  const reais = Math.trunc(centavos / 100);
  const resto = Math.abs(centavos % 100);
  if (resto === 0) return `R$\u00a0${reais}`;
  return `R$\u00a0${reais},${String(resto).padStart(2, "0")}`;
}
