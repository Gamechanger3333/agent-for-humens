-- FreelanceOps schema. Run this in the Supabase SQL editor of the project
-- referenced by SUPABASE_URL in agent/.env.

create table if not exists public.leads (
  id uuid primary key default gen_random_uuid(),
  client_name text not null,
  company text,
  email text,
  job_title text not null,
  job_description text,
  status text not null default 'proposal_sent'
    check (status in ('new', 'proposal_sent', 'in_conversation', 'won', 'lost')),
  last_contact_at timestamptz not null default now(),
  followup_count int not null default 0,
  notes text,
  created_at timestamptz not null default now()
);

create table if not exists public.proposals (
  id uuid primary key default gen_random_uuid(),
  lead_id uuid references public.leads(id) on delete set null,
  job_title text,
  job_description text not null,
  proposal_text text not null,
  matched_projects text[] not null default '{}',
  created_at timestamptz not null default now()
);

create table if not exists public.invoices (
  id uuid primary key default gen_random_uuid(),
  lead_id uuid references public.leads(id) on delete cascade,
  client_name text not null,
  amount numeric(12, 2) not null,
  currency text not null default 'USD',
  due_date date not null,
  paid boolean not null default false,
  created_at timestamptz not null default now()
);

grant select, insert, update, delete on public.leads to authenticated;
grant select, insert, update, delete on public.proposals to authenticated;
grant select, insert, update, delete on public.invoices to authenticated;
grant all on public.leads, public.proposals, public.invoices to service_role;

alter table public.leads enable row level security;
alter table public.proposals enable row level security;
alter table public.invoices enable row level security;

-- Single-operator studio app: authenticated users (you) manage everything.
create policy "authenticated manage leads" on public.leads
  for all to authenticated using (true) with check (true);
create policy "authenticated manage proposals" on public.proposals
  for all to authenticated using (true) with check (true);
create policy "authenticated manage invoices" on public.invoices
  for all to authenticated using (true) with check (true);
