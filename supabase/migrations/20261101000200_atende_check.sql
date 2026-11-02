-- Todo valor de pratos.atende precisa ser uma restrição conhecida (enum Restricao do backend).
alter table public.pratos
  add constraint pratos_atende_valido check (
    atende <@ array[
      'sem_lactose', 'sem_gluten', 'vegetariano', 'vegano',
      'sem_amendoim', 'sem_frutos_do_mar', 'sem_ovo'
    ]::text[]
  );
