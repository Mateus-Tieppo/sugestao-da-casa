-- Sobremesas e doces só aparecem quando a pessoa pede (Criterios.quer_doce).
alter table public.pratos
  add column doce boolean not null default false;
