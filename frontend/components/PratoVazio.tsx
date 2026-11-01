interface Props {
  /** Garfo e faca cruzados sobre o prato: a cozinha não respondeu. */
  talheres?: boolean;
}

/** Prato limpo, visto de cima. Sem resultado e falha usam o mesmo prato do início, só que vazio. */
export function PratoVazio({ talheres = false }: Props) {
  return (
    <div aria-hidden="true" className="prato prato-grande prato-vazio size-full">
      {talheres ? (
        <svg viewBox="0 0 200 200" className="absolute inset-0 size-full drop-shadow-[0_2px_3px_rgb(60_10_0/0.25)]">
          <g transform="rotate(38 100 100)" fill="#8a7566">
            <rect x="96.5" y="62" width="7" height="104" rx="3.5" />
            <rect x="85" y="30" width="3.2" height="40" rx="1.6" />
            <rect x="91.4" y="30" width="3.2" height="40" rx="1.6" />
            <rect x="97.8" y="30" width="3.2" height="40" rx="1.6" />
            <rect x="104.2" y="30" width="3.2" height="40" rx="1.6" />
            <path d="M85 64h22.4v6c0 6-5 9-11.2 9S85 76 85 70z" />
          </g>
          <g transform="rotate(-38 100 100)" fill="#8a7566">
            <rect x="96.5" y="70" width="7" height="96" rx="3.5" />
            <path d="M96.5 30c10 0 14 18 7 44h-7z" />
          </g>
        </svg>
      ) : null}
    </div>
  );
}
