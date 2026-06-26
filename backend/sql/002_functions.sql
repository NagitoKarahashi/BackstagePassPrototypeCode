create or replace function public.generate_ticket_serial()
returns text
language sql
as $$
  select 'TIX-' || upper(substr(replace(gen_random_uuid()::text, '-', ''), 1, 12));
$$;

create or replace function public.generate_qr_token()
returns text
language sql
as $$
  select encode(gen_random_bytes(16), 'hex');
$$;

create or replace function public.purchase_ticket(
  p_user_id uuid,
  p_event_id uuid,
  p_ticket_tier_id uuid,
  p_quantity integer,
  p_wallet_address text default null,
  p_device_id text default null,
  p_ip_address text default null
)
returns uuid
language plpgsql
as $$
declare
  v_order_id uuid;
  v_unit_price numeric(10,2);
  v_currency text;
  v_supply_total integer;
  v_supply_sold integer;
  v_sale_start timestamptz;
  v_sale_end timestamptz;
begin
  if p_quantity <= 0 then
    raise exception 'Quantity must be > 0';
  end if;

  select price, currency, supply_total, supply_sold, sale_start, sale_end
  into v_unit_price, v_currency, v_supply_total, v_supply_sold, v_sale_start, v_sale_end
  from public.ticket_tiers
  where id = p_ticket_tier_id and event_id = p_event_id
  for update;

  if not found then
    raise exception 'Ticket tier not found';
  end if;

  if v_sale_start is not null and now() < v_sale_start then
    raise exception 'Sale has not started';
  end if;

  if v_sale_end is not null and now() > v_sale_end then
    raise exception 'Sale has ended';
  end if;

  if (v_supply_total - v_supply_sold) < p_quantity then
    raise exception 'Not enough inventory';
  end if;

  insert into public.orders (user_id, event_id, total_amount, currency, status, wallet_address, device_id, ip_address)
  values (p_user_id, p_event_id, v_unit_price * p_quantity, v_currency, 'pending', p_wallet_address, p_device_id, p_ip_address)
  returning id into v_order_id;

  insert into public.order_items (order_id, ticket_tier_id, quantity, unit_price)
  values (v_order_id, p_ticket_tier_id, p_quantity, v_unit_price);

  update public.ticket_tiers
  set supply_sold = supply_sold + p_quantity
  where id = p_ticket_tier_id;

  return v_order_id;
end;
$$;

create or replace function public.issue_tickets_for_order(p_order_id uuid)
returns integer
language plpgsql
as $$
declare
  v_order record;
  v_item record;
  v_i integer;
  v_issued_count integer := 0;
begin
  select * into v_order from public.orders where id = p_order_id;
  if not found then
    raise exception 'Order not found';
  end if;

  if v_order.status not in ('paid') then
    raise exception 'Order must be paid before ticket issuance';
  end if;

  for v_item in
    select oi.*, tt.event_id
    from public.order_items oi
    join public.ticket_tiers tt on tt.id = oi.ticket_tier_id
    where oi.order_id = p_order_id
  loop
    for v_i in 1..v_item.quantity loop
      insert into public.tickets (order_id, event_id, owner_user_id, ticket_tier_id, serial_no, qr_token, wallet_address, status)
      values (p_order_id, v_item.event_id, v_order.user_id, v_item.ticket_tier_id, public.generate_ticket_serial(), public.generate_qr_token(), v_order.wallet_address, 'issued');
      v_issued_count := v_issued_count + 1;
    end loop;
  end loop;

  return v_issued_count;
end;
$$;

create or replace function public.check_in_ticket(
  p_qr_token text,
  p_scanned_by uuid default null,
  p_scanner_device_id text default null
)
returns text
language plpgsql
as $$
declare
  v_ticket record;
begin
  select * into v_ticket from public.tickets where qr_token = p_qr_token;

  if not found then
    insert into public.check_in_logs (ticket_id, scanned_by, scanner_device_id, scanned_qr_token, result, note)
    values (null, p_scanned_by, p_scanner_device_id, p_qr_token, 'invalid', 'QR token not found');
    return 'invalid';
  end if;

  if v_ticket.status = 'checked_in' then
    insert into public.check_in_logs (ticket_id, scanned_by, scanner_device_id, scanned_qr_token, result, note)
    values (v_ticket.id, p_scanned_by, p_scanner_device_id, p_qr_token, 'duplicate', 'Ticket already checked in');
    return 'duplicate';
  end if;

  if v_ticket.status in ('cancelled', 'flagged') then
    insert into public.check_in_logs (ticket_id, scanned_by, scanner_device_id, scanned_qr_token, result, note)
    values (v_ticket.id, p_scanned_by, p_scanner_device_id, p_qr_token, 'blocked', 'Ticket blocked');
    return 'blocked';
  end if;

  update public.tickets set status = 'checked_in', checked_in_at = now() where id = v_ticket.id;

  insert into public.check_in_logs (ticket_id, scanned_by, scanner_device_id, scanned_qr_token, result, note)
  values (v_ticket.id, p_scanned_by, p_scanner_device_id, p_qr_token, 'success', 'Check-in successful');

  return 'success';
end;
$$;
