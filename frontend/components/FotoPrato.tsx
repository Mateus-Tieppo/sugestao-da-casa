import Image from "next/image";

type Receita =
  "caldo" | "lamen" | "curry" | "salada" | "pizza" | "massa" | "doce" | "sushi" | "burger" | "bowl" | "feijao";

// Ordem importa: o primeiro termo que aparece no nome decide o desenho.
const TERMOS: [RegExp, Receita][] = [
  [/\b(lamen|yakisoba|pad thai|talharim)\b/, "lamen"],
  [/\b(caldo|sopa|canja|gaspacho|tom kha)\b/, "caldo"],
  [/\b(sushi|temaki|ceviche|rolinho|gyoza)\b/, "sushi"],
  [/\b(pizza|calzone|bruschetta)\b/, "pizza"],
  [/\b(burger|hamburguer|sanduiche|cachorro|wrap|esfiha|burrito|tacos|quesadilla|shawarma)\b/, "burger"],
  [/\b(brigadeiro|brownie|pudim|bolo|cookie|churros|mousse|torta|pe de moleque|sorbet)\b/, "doce"],
  [/\b(fettuccine|espaguete|penne|lasanha|nhoque|macarrao|risoto)\b/, "massa"],
  [/\b(salada|tabule|caprese)\b/, "salada"],
  [/\b(bowl|poke|tigela|acai|falafel|homus)\b/, "bowl"],
  [/\b(curry|moqueca|bobo|camarao|vatapa|acaraje)\b/, "curry"],
  [/\b(feij|chili|baiao|carne|costela|picanha|escondidinho|linguica|tropeiro)/, "feijao"],
];

const RESERVA: Receita[] = ["caldo", "curry", "bowl", "feijao", "salada"];

function normalizar(texto: string): string {
  return texto.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
}

export function receitaDoPrato(nome: string): Receita {
  const n = normalizar(nome);
  for (const [termo, receita] of TERMOS) if (termo.test(n)) return receita;
  let h = 0;
  for (const c of n) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  return RESERVA[h % RESERVA.length];
}

type Tamanho = "grande" | "medio" | "pequeno";

const CLASSE_TAMANHO: Record<Tamanho, string> = {
  grande: "prato-grande",
  medio: "",
  pequeno: "prato-pequeno",
};

interface Props {
  nome: string;
  fotoUrl: string | null;
  tamanho: Tamanho;
  /** Tamanho exibido, para o navegador escolher a foto certa (atributo sizes). */
  sizes: string;
  className?: string;
  preload?: boolean;
}

/** Prato visto de cima: foto real num prato creme, ou o desenho quando não há foto. */
export function FotoPrato({ nome, fotoUrl, tamanho, sizes, className = "", preload = false }: Props) {
  const base = `prato ${CLASSE_TAMANHO[tamanho]} ${className}`;
  if (!fotoUrl) {
    return <div aria-hidden="true" className={`${base} prato-${receitaDoPrato(nome)}`} />;
  }
  return (
    <div className={`${base} overflow-hidden bg-papel-funda`}>
      <Image src={fotoUrl} alt="" fill sizes={sizes} preload={preload} className="object-cover" />
      <span className="prato-aro" aria-hidden="true" />
    </div>
  );
}
