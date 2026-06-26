export type EventItem = {
  id: string;
  event_code: string;
  title: string;
  artist?: string | null;
  genre?: string | null;
  city?: string | null;
  country?: string | null;
  venue_name?: string | null;
  tags?: string[];
  start_time?: string | null;
  starts_at?: string | null;
  ends_at?: string | null;
  description?: string | null;
  price?: number | null;
  stock_total?: number | null;
  stock_left?: number | null;
  poster_url?: string | null;
  cover_url?: string | null;
  status?: string | null;
};

export type Profile = {
  id: string;
  display_name?: string | null;
  email?: string | null;
  username?: string | null;
  avatar_url?: string | null;
  bio?: string | null;
  city?: string | null;
  wallet_address?: string | null;
  preferred_genres?: string[];
  preferred_artists?: string[];
  fan_points?: number;
  following_count?: number;
  follower_count?: number;
};

export type Ticket = {
  id: string;
  user_id?: string;
  order_id?: string | null;
  event_id?: string | null;
  event_uuid?: string | null;
  token_id?: string | null;
  contract_address?: string | null;
  chain?: string | null;
  metadata?: Record<string, unknown> | null;
  metadata_uri?: string | null;
  qr_payload?: string | null;
  status: 'active' | 'used' | 'expired' | 'refunded' | string;
  is_listed?: boolean;
  transfer_locked?: boolean;
  resale_allowed?: boolean;
  last_transfer_at?: string | null;
  owner_wallet?: string | null;
  mint_status?: string | null;
  minted_at?: string | null;
  tx_hash?: string | null;
  created_at?: string | null;
  title?: string | null;
  artist?: string | null;
  city?: string | null;
  genre?: string | null;
  start_time?: string | null;
  poster_url?: string | null;
};

export type WalletMe = {
  wallet_address?: string | null;
  total_tickets: number;
  minted_tickets: number;
  listed_tickets: number;
};

export type WalletTicketDetail = {
  id: string;
  order_id?: string | null;
  event_id?: string | null;
  event_uuid?: string | null;
  title?: string | null;
  artist?: string | null;
  city?: string | null;
  genre?: string | null;
  start_time?: string | null;
  poster_url?: string | null;
  description?: string | null;
  status: string;
  token_id?: string | null;
  contract_address?: string | null;
  chain?: string | null;
  owner_wallet?: string | null;
  mint_status?: string | null;
  minted_at?: string | null;
  tx_hash?: string | null;
  metadata_uri?: string | null;
  metadata?: Record<string, unknown> | null;
  is_listed?: boolean;
  active_listing?: MarketplaceListing | null;
  created_at?: string | null;
};

export type TicketEventBrief = {
  id: string;
  event_code?: string | null;
  title?: string | null;
  artist?: string | null;
  genre?: string | null;
  city?: string | null;
  start_time?: string | null;
  poster_url?: string | null;
};

export type TicketHistoryItem = {
  id: string;
  ticket_id: string;
  from_user_id?: string | null;
  to_user_id?: string | null;
  from_wallet_address?: string | null;
  to_wallet_address?: string | null;
  transfer_type: string;
  transfer_status: string;
  risk_level?: string | null;
  risk_type?: string | null;
  note?: string | null;
  created_at?: string | null;
};

export type Web3HistoryItem = {
  id: string;
  ticket_id: string;
  from_user_id?: string | null;
  to_user_id?: string | null;
  from_wallet?: string | null;
  to_wallet?: string | null;
  action: string;
  tx_hash?: string | null;
  note?: string | null;
  created_at?: string | null;
};

export type TicketDetailResponse = {
  ticket: Ticket;
  event?: TicketEventBrief | null;
  current_listing?: MarketplaceListing | null;
  history_preview?: TicketHistoryItem[];
};

export type TicketHistoryResponse = {
  items: TicketHistoryItem[];
};

export type TransferTicketPayload = {
  to_user_id: string;
  to_wallet_address?: string | null;
  note?: string | null;
  device_id?: string | null;
  ip_address?: string | null;
};

export type TicketMarketStatusResponse = {
  ticket_id: string;
  is_listed: boolean;
  transfer_locked: boolean;
  resale_allowed: boolean;
  listing?: MarketplaceListing | null;
};

export type MarketplaceListing = {
  id: string;
  ticket_id: string;
  seller_user_id: string;
  seller_wallet?: string | null;
  buyer_user_id?: string | null;
  buyer_wallet?: string | null;
  listing_price: number;
  currency?: string | null;
  status: string;
  expires_at?: string | null;
  sold_at?: string | null;
  cancelled_at?: string | null;
  created_at?: string | null;
  tx_hash?: string | null;
  ticket_status?: string | null;
  event_uuid?: string | null;
  owner_wallet?: string | null;
  mint_status?: string | null;
  token_id?: string | null;
  contract_address?: string | null;
  chain?: string | null;
};

export type MarketplaceListingListResponse = {
  items: MarketplaceListing[];
};

export type CreateListingPayload = {
  ticket_id: string;
  listing_price: number;
  currency?: string;
  expires_at?: string | null;
};

export type ChatRoom = {
  id: string;
  event_id: string;
  room_name: string;
  room_type: string;
  created_at?: string | null;
};

export type ChatMessage = {
  id: string;
  room_id: string;
  sender_user_id: string;
  message_text: string;
  created_at?: string | null;
  edited_at?: string | null;
  is_pinned?: boolean;
};

export type RewardMission = {
  mission_id: string;
  code: string;
  title: string;
  description?: string | null;
  category: string;
  progress: number;
  target_value: number;
  reward_points: number;
  status: string;
  days_left?: number | null;
};