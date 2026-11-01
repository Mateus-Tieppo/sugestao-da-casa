-- Cardápio do Sugestão da Casa: leitura pública, sem escrita para anon/authenticated.

create table public.restaurantes (
  id uuid primary key default gen_random_uuid(),
  nome text not null,
  taxa_entrega_centavos int not null check (taxa_entrega_centavos >= 0),
  tempo_entrega_min int not null check (tempo_entrega_min > 0)
);

create table public.pratos (
  id uuid primary key default gen_random_uuid(),
  restaurante_id uuid not null references public.restaurantes (id) on delete cascade,
  nome text not null,
  descricao text not null,
  preco_centavos int not null check (preco_centavos > 0),
  tempo_preparo_min int not null default 0 check (tempo_preparo_min >= 0),
  ingredientes text[] not null,
  atende text[] not null,
  temperatura smallint check (temperatura between 0 and 100),
  peso smallint check (peso between 0 and 100),
  picancia smallint check (picancia between 0 and 100),
  conforto smallint check (conforto between 0 and 100),
  foto_url text
);

create index pratos_restaurante_id_idx on public.pratos (restaurante_id);

alter table public.restaurantes enable row level security;
alter table public.pratos enable row level security;

create policy "restaurantes: leitura pública"
  on public.restaurantes for select
  to anon, authenticated
  using (true);

create policy "pratos: leitura pública"
  on public.pratos for select
  to anon, authenticated
  using (true);
