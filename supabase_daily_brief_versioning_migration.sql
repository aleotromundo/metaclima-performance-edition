-- MetaClima · Versionado por lotes diarios del informe meteorológico
-- Ejecutar DESPUÉS de supabase_daily_brief_schema.sql.
-- No contiene claves secretas.

-- 1) Cada generación pertenece a un lote diario y a una franja de dos horas.
alter table public.daily_briefs
  add column if not exists batch_key text,
  add column if not exists slot_key text,
  add column if not exists batch_status text not null default 'staging',
  add column if not exists published_at timestamptz;

update public.daily_briefs
set batch_key = coalesce(batch_key, local_date::text),
    slot_key = coalesce(slot_key, to_char(generated_at at time zone 'UTC', 'YYYYMMDD-HH24')),
    batch_status = case when is_current then 'published' else 'staging' end
where batch_key is null or slot_key is null;

alter table public.daily_briefs
  alter column batch_key set not null;

alter table public.daily_briefs
  drop constraint if exists daily_briefs_batch_status_check;
alter table public.daily_briefs
  add constraint daily_briefs_batch_status_check
  check (batch_status in ('staging', 'published', 'archived'));

create index if not exists daily_briefs_batch_lookup_idx
  on public.daily_briefs (location_key, batch_key, generated_at desc);

create unique index if not exists daily_briefs_one_slot_per_batch
  on public.daily_briefs (location_key, batch_key, slot_key);

-- 2) Un puntero pequeño determina qué lote ve públicamente la página.
create table if not exists public.daily_brief_publications (
  location_key text primary key,
  batch_key text not null,
  published_local_date date not null,
  published_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.daily_brief_publications enable row level security;

drop policy if exists "brief publication pointer is publicly readable" on public.daily_brief_publications;
create policy "brief publication pointer is publicly readable"
on public.daily_brief_publications for select
to anon, authenticated
using (true);

drop policy if exists "brief publication pointer browser insert" on public.daily_brief_publications;
drop policy if exists "brief publication pointer browser update" on public.daily_brief_publications;
drop policy if exists "brief publication pointer browser delete" on public.daily_brief_publications;

-- 3) La vista pública deja de mirar la última fila generada.
--    Solo expone el lote que el proceso automático publicó explícitamente.
create or replace view public.current_weather_brief as
select
  d.id,
  d.location_key,
  d.location_label,
  d.latitude,
  d.longitude,
  d.local_date,
  d.batch_key,
  d.slot_key,
  d.dialogue,
  d.audio_path,
  d.audio_mime_type,
  d.duration_seconds,
  d.voice_provider,
  d.voice_name,
  d.generated_at,
  d.expires_at,
  d.published_at
from public.daily_briefs d
join public.daily_brief_publications p
  on p.location_key = d.location_key
 and p.batch_key = d.batch_key
where d.batch_status = 'published';

grant select on public.daily_brief_publications to anon, authenticated;
grant select on public.current_weather_brief to anon, authenticated;

-- 4) El backend llama esta función SOLO cuando el lote está completo.
--    Durante el día, las generaciones nuevas quedan en staging.
--    La publicación del lote se hace en una sola operación lógica.
create or replace function public.publish_daily_brief_batch(
  p_location_key text,
  p_batch_key text,
  p_published_local_date date
)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  if not exists (
    select 1 from public.daily_briefs
    where location_key = p_location_key
      and batch_key = p_batch_key
  ) then
    raise exception 'No existe el lote indicado';
  end if;

  -- Nunca se pisa un audio durante el día: primero se archiva lo anterior.
  update public.daily_briefs
     set is_current = false,
         batch_status = 'archived'
   where location_key = p_location_key
     and batch_status = 'published';

  update public.daily_briefs
     set is_current = true,
         batch_status = 'published',
         published_at = now()
   where location_key = p_location_key
     and batch_key = p_batch_key;

  insert into public.daily_brief_publications (
    location_key, batch_key, published_local_date, published_at, updated_at
  ) values (
    p_location_key, p_batch_key, p_published_local_date, now(), now()
  )
  on conflict (location_key) do update set
    batch_key = excluded.batch_key,
    published_local_date = excluded.published_local_date,
    published_at = excluded.published_at,
    updated_at = now();
end;
$$;

revoke all on function public.publish_daily_brief_batch(text, text, date) from public, anon, authenticated;
-- El proceso server-side protegido debe recibir permiso explícito para ejecutarla.
-- Con service_role podrá invocarla sin exponer credenciales en index.html.

-- 5) Flujo operativo esperado:
--    a) Al comenzar el día, crear un batch_key = YYYY-MM-DD por ubicación.
--    b) Cada dos horas generar un MP3 nuevo y guardarlo en una ruta única:
--       weather-briefs/<location_key>/<batch_key>/<slot_key>.mp3
--    c) Insertar cada versión como batch_status='staging', is_current=false.
--    d) No modificar el puntero daily_brief_publications mientras el lote está en curso.
--    e) Al comenzar el día siguiente, cerrar el lote anterior y publicar el nuevo lote completo.
--    f) La web solo consulta current_weather_brief, por lo que no ve versiones parciales.
--    g) Los lotes antiguos quedan archivados y pueden limpiarse con una tarea de retención posterior.
