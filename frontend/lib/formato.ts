/** Formata centavos como reais: "R$ 32" (inteiro) ou "R$ 22,50". */
export function formatarReais(centavos: number): string {
  const reais = Math.trunc(centavos / 100);
  const resto = Math.abs(centavos % 100);
  if (resto === 0) return `R$ ${reais}`;
  return `R$ ${reais},${String(resto).padStart(2, "0")}`;
}
