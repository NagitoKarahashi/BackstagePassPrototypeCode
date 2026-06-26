'use client';

import { useEffect, useMemo, useState } from 'react';
import { PageHeader } from '@/components/common/PageHeader';
import {
  buyListing,
  cancelListing,
  getMarketplaceListings,
  getMyMarketplaceListings,
} from '@/lib/api/marketplace';
import { getCurrentUserId } from '@/lib/auth/session';
import type { MarketplaceListing } from '@/lib/types';

function formatDate(value?: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function shortAddr(value?: string | null) {
  if (!value) return '—';
  if (value.length <= 18) return value;
  return `${value.slice(0, 8)}...${value.slice(-6)}`;
}

function SmallTag({
  label,
  tone = 'gray',
}: {
  label: string;
  tone?: 'gray' | 'blue' | 'gold' | 'green' | 'red';
}) {
  let bg = 'rgba(255,255,255,0.08)';
  let color = '#E8E8E8';

  if (tone === 'blue') {
    bg = 'rgba(125,180,255,0.16)';
    color = '#BBD3FF';
  } else if (tone === 'gold') {
    bg = 'rgba(255,204,102,0.16)';
    color = '#FFD27C';
  } else if (tone === 'green') {
    bg = 'rgba(66,184,131,0.18)';
    color = '#A9FFCB';
  } else if (tone === 'red') {
    bg = 'rgba(255,99,99,0.18)';
    color = '#FFB0B0';
  }

  return (
    <span
      style={{
        padding: '4px 8px',
        borderRadius: 999,
        fontSize: 11,
        fontWeight: 700,
        background: bg,
        color,
      }}
    >
      {label}
    </span>
  );
}

function statusTone(status?: string | null): 'gray' | 'green' | 'gold' | 'red' {
  const normalized = (status || '').toLowerCase();
  if (normalized === 'active') return 'green';
  if (normalized === 'sold') return 'gold';
  if (normalized === 'cancelled') return 'red';
  return 'gray';
}

function ListingCard({
  item,
  canBuy,
  canCancel,
  busy,
  onBuy,
  onCancel,
}: {
  item: MarketplaceListing;
  canBuy: boolean;
  canCancel: boolean;
  busy: boolean;
  onBuy: () => void;
  onCancel: () => void;
}) {
  const mintStatus = (item.mint_status || 'not_minted').toLowerCase();
  const listingStatus = (item.status || 'unknown').toLowerCase();
  const ticketStatus = (item.ticket_status || 'unknown').toLowerCase();

  return (
    <div className="card" key={item.id}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          gap: 12,
          marginBottom: 12,
          alignItems: 'flex-start',
        }}
      >
        <div>
          <div style={{ fontSize: 20, fontWeight: 800 }}>
            {item.token_id ? `NFT #${item.token_id}` : `Listing #${item.id.slice(0, 8)}`}
          </div>
          <div className="muted small" style={{ marginTop: 4 }}>
            Ticket ID: {item.ticket_id}
          </div>
        </div>

        <SmallTag
          label={`Listing: ${listingStatus}`}
          tone={statusTone(listingStatus)}
        />
      </div>

      <div style={{ marginBottom: 8 }}>
        Price: <strong>{item.listing_price} {item.currency || 'USD'}</strong>
      </div>

      <div className="muted small">Seller: {item.seller_user_id}</div>
      <div className="muted small">Seller Wallet: {shortAddr(item.seller_wallet)}</div>
      <div className="muted small">Owner Wallet: {shortAddr(item.owner_wallet)}</div>
      <div className="muted small">Created: {formatDate(item.created_at)}</div>
      <div className="muted small">Expires: {formatDate(item.expires_at)}</div>
      <div className="muted small">Sold At: {formatDate(item.sold_at)}</div>
      <div className="muted small">Cancelled At: {formatDate(item.cancelled_at)}</div>

      <div style={{ marginTop: 12, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <SmallTag
          label={mintStatus === 'minted' ? 'Minted' : 'Not Minted'}
          tone={mintStatus === 'minted' ? 'blue' : 'gray'}
        />
        {item.chain ? <SmallTag label={item.chain} tone="gold" /> : null}
        <SmallTag
          label={`Ticket: ${ticketStatus}`}
          tone={statusTone(ticketStatus)}
        />
      </div>

      <div className="muted small" style={{ marginTop: 12 }}>
        Tx: {item.tx_hash || '—'}
      </div>

      <div style={{ marginTop: 16, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
        {canBuy ? (
          <button className="btn" onClick={onBuy} disabled={busy}>
            {busy ? 'Processing...' : 'Buy Listing'}
          </button>
        ) : null}

        {canCancel ? (
          <button className="btn ghost" onClick={onCancel} disabled={busy}>
            {busy ? 'Working...' : 'Cancel Listing'}
          </button>
        ) : null}
      </div>
    </div>
  );
}

export default function MarketPage() {
  const [items, setItems] = useState<MarketplaceListing[]>([]);
  const [myItems, setMyItems] = useState<MarketplaceListing[]>([]);
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [myFilter, setMyFilter] = useState<'all' | 'active' | 'cancelled' | 'sold'>('all');

  async function reload() {
    try {
      setLoading(true);
      const [userId, publicData, myData] = await Promise.all([
        getCurrentUserId(),
        getMarketplaceListings(),
        getMyMarketplaceListings(),
      ]);

      setCurrentUserId(userId || null);
      setItems((publicData.items || []) as MarketplaceListing[]);
      setMyItems((myData.items || []) as MarketplaceListing[]);
      setError('');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load marketplace');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void reload();
  }, []);

  async function handleBuy(listingId: string) {
    try {
      setBusyId(listingId);
      await buyListing(listingId);
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to buy listing');
    } finally {
      setBusyId(null);
    }
  }

  async function handleCancel(listingId: string) {
    try {
      setBusyId(listingId);
      await cancelListing(listingId);
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to cancel listing');
    } finally {
      setBusyId(null);
    }
  }

  const publicItems = useMemo(() => {
    return items.filter((item) => (item.status || '').toLowerCase() === 'active');
  }, [items]);

  const filteredMyItems = useMemo(() => {
    if (myFilter === 'all') return myItems;
    return myItems.filter((item) => (item.status || '').toLowerCase() === myFilter);
  }, [myItems, myFilter]);

  return (
    <div>
      <PageHeader
        title="Marketplace"
        subtitle="Prototype secondary market for ticket resale, wallet ownership, and NFT-style metadata."
      />

      {loading ? <div className="card">Loading marketplace...</div> : null}
      {error ? <div className="card">{error}</div> : null}

      <div style={{ display: 'grid', gap: 24 }}>
        <section>
          <div style={{ fontSize: 22, fontWeight: 800, marginBottom: 14 }}>Public Listings</div>

          {publicItems.length === 0 && !loading ? (
            <div className="card">No active listings right now.</div>
          ) : (
            <div className="grid grid-2">
              {publicItems.map((item) => {
                const isSeller = !!currentUserId && item.seller_user_id === currentUserId;
                const canBuy =
                  !isSeller &&
                  (item.status || '').toLowerCase() === 'active';

                return (
                  <ListingCard
                    key={item.id}
                    item={item}
                    canBuy={canBuy}
                    canCancel={false}
                    busy={busyId === item.id}
                    onBuy={() => void handleBuy(item.id)}
                    onCancel={() => void handleCancel(item.id)}
                  />
                );
              })}
            </div>
          )}
        </section>

        <section>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              gap: 16,
              alignItems: 'center',
              marginBottom: 14,
              flexWrap: 'wrap',
            }}
          >
            <div style={{ fontSize: 22, fontWeight: 800 }}>My Listings</div>

            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {(['all', 'active', 'cancelled', 'sold'] as const).map((key) => (
                <button
                  key={key}
                  className={myFilter === key ? 'btn' : 'btn ghost'}
                  onClick={() => setMyFilter(key)}
                >
                  {key}
                </button>
              ))}
            </div>
          </div>

          {filteredMyItems.length === 0 && !loading ? (
            <div className="card">No listings found for this filter.</div>
          ) : (
            <div className="grid grid-2">
              {filteredMyItems.map((item) => {
                const listingStatus = (item.status || '').toLowerCase();
                const canCancel = listingStatus === 'active';

                return (
                  <ListingCard
                    key={item.id}
                    item={item}
                    canBuy={false}
                    canCancel={canCancel}
                    busy={busyId === item.id}
                    onBuy={() => void handleBuy(item.id)}
                    onCancel={() => void handleCancel(item.id)}
                  />
                );
              })}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}