-- =========================================================
-- Phase 1 social/community extension
-- For PRD features:
-- - fan community chat
-- - user profile & preferences
-- - off-chain fan points
-- =========================================================

create extension if not exists pgcrypto;

-- =========================================================
-- 1) user_preferences
-- each user can store preferred artists / genres / cities
-- =========================================================
create table if not exists public.user_preferences (
  user_id uuid primary key references public.profiles(id) on delete cascade,
  preferred_artists text[] not null default '{}',
  preferred_genres text[] not null default '{}',
  preferred_cities text[] not null default '{}',
  updated_at timestamptz not null default now()
);

-- =========================================================
-- 2) user_follows
-- user follows another user / artist / organizer
-- keep it simple for Phase 1
-- =========================================================
create table if not exists public.user_follows (
  id uuid primary key default gen_random_uuid(),
  follower_user_id uuid not null references public.profiles(id) on delete cascade,
  followee_user_id uuid not null references public.profiles(id) on delete cascade,
  created_at timestamptz not null default now(),
  constraint uq_user_follow unique (follower_user_id, followee_user_id),
  constraint chk_not_self_follow check (follower_user_id <> followee_user_id)
);

create index if not exists idx_user_follows_follower on public.user_follows(follower_user_id);
create index if not exists idx_user_follows_followee on public.user_follows(followee_user_id);

-- =========================================================
-- 3) fan_points
-- off-chain reward summary per user
-- =========================================================
create table if not exists public.fan_points (
  user_id uuid primary key references public.profiles(id) on delete cascade,
  points_balance integer not null default 0 check (points_balance >= 0),
  lifetime_points integer not null default 0 check (lifetime_points >= 0),
  level text not null default 'rookie',
  updated_at timestamptz not null default now()
);

-- =========================================================
-- 4) fan_point_logs
-- record how points are earned
-- =========================================================
create table if not exists public.fan_point_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  event_id uuid references public.events(id) on delete set null,
  source_type text not null
    check (source_type in ('ticket_purchase', 'check_in', 'chat_message', 'bonus', 'manual_adjustment')),
  points_delta integer not null,
  note text,
  created_at timestamptz not null default now()
);

create index if not exists idx_fan_point_logs_user_id on public.fan_point_logs(user_id);
create index if not exists idx_fan_point_logs_event_id on public.fan_point_logs(event_id);

-- =========================================================
-- 5) chat_rooms
-- one event usually has one room
-- =========================================================
create table if not exists public.chat_rooms (
  id uuid primary key default gen_random_uuid(),
  event_id uuid not null unique references public.events(id) on delete cascade,
  room_name text not null,
  room_type text not null default 'event'
    check (room_type in ('event')),
  created_at timestamptz not null default now()
);

create index if not exists idx_chat_rooms_event_id on public.chat_rooms(event_id);

-- =========================================================
-- 6) chat_room_members
-- who is allowed in the room
-- =========================================================
create table if not exists public.chat_room_members (
  id uuid primary key default gen_random_uuid(),
  room_id uuid not null references public.chat_rooms(id) on delete cascade,
  user_id uuid not null references public.profiles(id) on delete cascade,
  role text not null default 'member'
    check (role in ('member', 'moderator', 'organizer')),
  joined_at timestamptz not null default now(),
  constraint uq_chat_room_member unique (room_id, user_id)
);

create index if not exists idx_chat_room_members_room_id on public.chat_room_members(room_id);
create index if not exists idx_chat_room_members_user_id on public.chat_room_members(user_id);

-- =========================================================
-- 7) chat_messages
-- basic text messages for Phase 1
-- =========================================================
create table if not exists public.chat_messages (
  id uuid primary key default gen_random_uuid(),
  room_id uuid not null references public.chat_rooms(id) on delete cascade,
  sender_user_id uuid not null references public.profiles(id) on delete cascade,
  message_text text not null,
  is_pinned boolean not null default false,
  created_at timestamptz not null default now(),
  edited_at timestamptz
);

create index if not exists idx_chat_messages_room_id on public.chat_messages(room_id);
create index if not exists idx_chat_messages_sender_user_id on public.chat_messages(sender_user_id);
create index if not exists idx_chat_messages_created_at on public.chat_messages(created_at);

-- =========================================================
-- 8) chat_message_reactions
-- simplified emoji reaction support
-- =========================================================
create table if not exists public.chat_message_reactions (
  id uuid primary key default gen_random_uuid(),
  message_id uuid not null references public.chat_messages(id) on delete cascade,
  user_id uuid not null references public.profiles(id) on delete cascade,
  emoji text not null,
  created_at timestamptz not null default now(),
  constraint uq_message_reaction unique (message_id, user_id, emoji)
);

create index if not exists idx_chat_message_reactions_message_id on public.chat_message_reactions(message_id);

-- =========================================================
-- 9) optional organizer_profiles
-- lightweight version for PRD organizer page
-- =========================================================
create table if not exists public.organizer_profiles (
  id uuid primary key default gen_random_uuid(),
  owner_user_id uuid references public.profiles(id) on delete set null,
  display_name text not null,
  bio text,
  avatar_url text,
  created_at timestamptz not null default now()
);

-- if you want, later events can reference organizer_profiles(id)
-- for now keep it optional and simple

-- =========================================================
-- 10) auto-create chat room for each new event
-- =========================================================
create or replace function public.create_event_chat_room()
returns trigger
language plpgsql
as $$
begin
  insert into public.chat_rooms (event_id, room_name, room_type)
  values (new.id, new.title || ' Chat', 'event')
  on conflict (event_id) do nothing;

  return new;
end;
$$;

drop trigger if exists trg_create_event_chat_room on public.events;

create trigger trg_create_event_chat_room
after insert on public.events
for each row
execute function public.create_event_chat_room();

-- =========================================================
-- 11) auto-join purchaser to event chat after ticket issuance
-- based on issued tickets
-- =========================================================
create or replace function public.join_event_chat_on_ticket_issue()
returns trigger
language plpgsql
as $$
declare
  v_room_id uuid;
begin
  select id into v_room_id
  from public.chat_rooms
  where event_id = new.event_id
  limit 1;

  if v_room_id is not null then
    insert into public.chat_room_members (room_id, user_id, role)
    values (v_room_id, new.owner_user_id, 'member')
    on conflict (room_id, user_id) do nothing;
  end if;

  return new;
end;
$$;

drop trigger if exists trg_join_event_chat_on_ticket_issue on public.tickets;

create trigger trg_join_event_chat_on_ticket_issue
after insert on public.tickets
for each row
execute function public.join_event_chat_on_ticket_issue();