create table if not exists public.support_enquiries (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  category text not null,
  subject text not null,
  message text not null,
  order_id uuid null,
  event_uuid uuid null,
  ticket_id uuid null,
  status text not null default 'open',
  source text not null default 'manual',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),

  constraint support_enquiries_category_check check (
    category in (
      'general',
      'refund',
      'transfer',
      'ticket',
      'event',
      'risk',
      'account',
      'technical'
    )
  ),
  constraint support_enquiries_status_check check (
    status in ('open', 'in_review', 'resolved', 'closed')
  )
);

create index if not exists idx_support_enquiries_user_id
  on public.support_enquiries(user_id);

create index if not exists idx_support_enquiries_created_at
  on public.support_enquiries(created_at desc);

create or replace function public.set_support_enquiries_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists trg_support_enquiries_updated_at on public.support_enquiries;

create trigger trg_support_enquiries_updated_at
before update on public.support_enquiries
for each row
execute function public.set_support_enquiries_updated_at();