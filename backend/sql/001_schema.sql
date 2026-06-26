create extension if not exists pgcrypto;

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  email text unique,
  wallet_address text,
  created_at timestamptz not null default now()
);

create table if not exists public.events (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  artist text,
  genre text,
  city text,
  venue_name text,
  venue_address text,
  description text,
  cover_image_url text,
  start_time timestamptz not null,
  end_time timestamptz,
  status text not null default 'draft' check (status in ('draft', 'published', 'sold_out', 'completed', 'cancelled')),
  created_at timestamptz not null default now()
);

create table if not exists public.ticket_tiers (
  id uuid primary key default gen_random_uuid(),
  event_id uuid not null references public.events(id) on delete cascade,
  name text not null,
  price numeric(10,2) not null check (price >= 0),
  currency text not null default 'GBP',
  supply_total integer not null check (supply_total >= 0),
  supply_reserved integer not null default 0 check (supply_reserved >= 0),
  supply_sold integer not null default 0 check (supply_sold >= 0),
  sale_start timestamptz,
  sale_end timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists public.orders (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete restrict,
  event_id uuid not null references public.events(id) on delete restrict,
  total_amount numeric(10,2) not null check (total_amount >= 0),
  currency text not null default 'GBP',
  status text not null default 'pending' check (status in ('pending', 'paid', 'failed', 'cancelled', 'refunded', 'flagged', 'under_review')),
  payment_ref text,
  wallet_address text,
  fraud_score numeric(6,4),
  risk_level text check (risk_level in ('low', 'medium', 'high')),
  device_id text,
  ip_address text,
  created_at timestamptz not null default now()
);

create table if not exists public.order_items (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null references public.orders(id) on delete cascade,
  ticket_tier_id uuid not null references public.ticket_tiers(id) on delete restrict,
  quantity integer not null check (quantity > 0),
  unit_price numeric(10,2) not null check (unit_price >= 0)
);

create table if not exists public.tickets (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null references public.orders(id) on delete cascade,
  event_id uuid not null references public.events(id) on delete restrict,
  owner_user_id uuid not null references public.profiles(id) on delete restrict,
  ticket_tier_id uuid not null references public.ticket_tiers(id) on delete restrict,
  serial_no text not null unique,
  qr_token text not null unique,
  nft_token_id text,
  wallet_address text,
  status text not null default 'issued' check (status in ('issued', 'checked_in', 'transferred', 'cancelled', 'flagged')),
  issued_at timestamptz not null default now(),
  checked_in_at timestamptz
);

create table if not exists public.fraud_signals (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null references public.orders(id) on delete cascade,
  signal_type text not null,
  signal_value text,
  weight numeric(6,4) not null default 0,
  created_at timestamptz not null default now()
);

create table if not exists public.fraud_reviews (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null references public.orders(id) on delete cascade,
  reviewer_id uuid references public.profiles(id) on delete set null,
  decision text not null check (decision in ('approve', 'reject', 'hold')),
  reason text,
  reviewed_at timestamptz not null default now()
);

create table if not exists public.appeals (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null references public.orders(id) on delete cascade,
  user_id uuid not null references public.profiles(id) on delete cascade,
  message text not null,
  status text not null default 'open' check (status in ('open', 'reviewing', 'resolved', 'rejected')),
  created_at timestamptz not null default now(),
  resolved_at timestamptz
);

create table if not exists public.check_in_logs (
  id uuid primary key default gen_random_uuid(),
  ticket_id uuid references public.tickets(id) on delete set null,
  scanned_by uuid references public.profiles(id) on delete set null,
  scanner_device_id text,
  scanned_qr_token text,
  scanned_at timestamptz not null default now(),
  result text not null check (result in ('success', 'duplicate', 'invalid', 'blocked')),
  note text
);
