'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { PageHeader } from '@/components/common/PageHeader';
import { getMyProfile } from '@/lib/api/profiles';
import { getMeOverview, getMeHistory } from '@/lib/api/me';
import { rewardsApi } from '@/lib/api/rewards';
import { getWalletMe } from '@/lib/api/wallet';
import { listEvents } from '@/lib/api/events';

type Profile = {
  id: string;
  display_name?: string | null;
  username?: string | null;
  email?: string | null;
  city?: string | null;
  preferred_genres?: string[];
  preferred_artists?: string[];
  fan_points?: number;
  following_count?: number;
  follower_count?: number;
};

type OverviewLike = {
  fan_points?: number;
  ticket_count?: number;
  order_count?: number;
  following_count?: number;
  follower_count?: number;
  recent_orders?: unknown[];
  recent_tickets?: unknown[];
  orders?: unknown[];
  tickets?: unknown[];
};

type HistoryLike = {
  orders?: unknown[];
  tickets?: unknown[];
};

type RewardSummary = {
  fan_points?: number;
  badge_count?: number;
  ledger_count?: number;
};

type WalletSummary = {
  wallet_address?: string | null;
  total_tickets?: number;
  minted_tickets?: number;
  listed_tickets?: number;
};

type EventItem = {
  id: string;
  title?: string;
  artist?: string;
  city?: string;
  genre?: string;
  poster_url?: string | null;
  price?: number | null;
  stock_left?: number | null;
  start_time?: string | null;
};

function normalizeEventList(data: any): EventItem[] {
  if (Array.isArray(data)) return data;
  if (data && typeof data === 'object') {
    if (Array.isArray(data.items)) return data.items;
    if (Array.isArray(data.data)) return data.data;
    if (Array.isArray(data.events)) return data.events;
  }
  return [];
}

function buildDisplayName(profile: Profile | null) {
  if (!profile) return 'Backstage Pass User';

  const candidates = [
    profile.display_name,
    profile.username,
    profile.email,
  ].filter(Boolean) as string[];

  const cleaned = candidates.find((v) => !v.startsWith('did:privy:'));
  return cleaned || 'Backstage Pass User';
}

function formatDate(value?: string | null) {
  if (!value) return 'TBD';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString();
}

function HeroStat({
  label,
  value,
  hint,
}: {
  label: string;
  value: string | number;
  hint?: string;
}) {
  return (
    <div className="card">
      <div style={{ fontSize: 13, opacity: 0.7, marginBottom: 8 }}>{label}</div>
      <div style={{ fontSize: 30, fontWeight: 800, lineHeight: 1.1 }}>{value}</div>
      {hint ? <div style={{ fontSize: 13, opacity: 0.65, marginTop: 10 }}>{hint}</div> : null}
    </div>
  );
}

function EventMiniCard({ event }: { event: EventItem }) {
  return (
    <Link
      href={`/events/${event.id}`}
      className="card"
      style={{ display: 'block', textDecoration: 'none', color: 'inherit' }}
    >
      <div
        style={{
          width: '100%',
          height: 150,
          borderRadius: 18,
          overflow: 'hidden',
          background: 'rgba(255,255,255,0.06)',
          marginBottom: 14,
          display: 'grid',
          placeItems: 'center',
        }}
      >
        {event.poster_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={event.poster_url}
            alt={event.title || 'Event poster'}
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
          />
        ) : (
          <div style={{ opacity: 0.45, fontWeight: 700 }}>{event.title || 'Event'}</div>
        )}
      </div>

      <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>
        {event.title || 'Untitled event'}
      </div>
      <div style={{ opacity: 0.72, marginBottom: 6 }}>
        {event.artist || 'Unknown artist'} {event.city ? `· ${event.city}` : ''}
      </div>
      <div style={{ opacity: 0.72, marginBottom: 6 }}>
        {event.genre || 'Genre TBD'} · {formatDate(event.start_time)}
      </div>
      <div style={{ opacity: 0.72 }}>
        {event.price ? `$${event.price}` : 'TBD'} {typeof event.stock_left === 'number' ? `· ${event.stock_left} left` : ''}
      </div>
    </Link>
  );
}

export default function DashboardPage() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [overview, setOverview] = useState<OverviewLike | null>(null);
  const [history, setHistory] = useState<HistoryLike | null>(null);
  const [rewardSummary, setRewardSummary] = useState<RewardSummary | null>(null);
  const [walletSummary, setWalletSummary] = useState<WalletSummary | null>(null);
  const [recommended, setRecommended] = useState<EventItem[]>([]);
  const [nearby, setNearby] = useState<EventItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        setError('');

        const [profileData, overviewData, historyData, rewardData, walletData] = await Promise.all([
          getMyProfile(),
          getMeOverview().catch(() => null),
          getMeHistory().catch(() => null),
          rewardsApi.summary().catch(() => null),
          getWalletMe().catch(() => null),
        ]);

        setProfile((profileData as Profile) || null);
        setOverview((overviewData as OverviewLike) || null);
        setHistory((historyData as HistoryLike) || null);
        setRewardSummary((rewardData as RewardSummary) || null);
        setWalletSummary((walletData as WalletSummary) || null);

        const city = (profileData as Profile | null)?.city || '';
        const genres = ((profileData as Profile | null)?.preferred_genres || []).join(',');

        const [recommendedRes, nearbyRes] = await Promise.all([
          listEvents({
            only_available: true,
            limit: 3,
            genre: genres || undefined,
          }).catch(() => ({ items: [] })),
          listEvents({
            only_available: true,
            limit: 3,
            city: city || undefined,
          }).catch(() => ({ items: [] })),
        ]);

        setRecommended(normalizeEventList(recommendedRes).slice(0, 3));
        setNearby(normalizeEventList(nearbyRes).slice(0, 3));
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load dashboard');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const displayName = useMemo(() => buildDisplayName(profile), [profile]);

  const fanPoints =
    rewardSummary?.fan_points ??
    overview?.fan_points ??
    profile?.fan_points ??
    0;

  const ticketCount =
    walletSummary?.total_tickets ??
    overview?.ticket_count ??
    (Array.isArray(history?.tickets) ? history!.tickets!.length : undefined) ??
    (Array.isArray(overview?.recent_tickets) ? overview!.recent_tickets!.length : undefined) ??
    (Array.isArray(overview?.tickets) ? overview!.tickets!.length : undefined) ??
    0;

  const orderCount =
    (Array.isArray(history?.orders) ? history!.orders!.length : undefined) ??
    overview?.order_count ??
    (Array.isArray(overview?.recent_orders) ? overview!.recent_orders!.length : undefined) ??
    (Array.isArray(overview?.orders) ? overview!.orders!.length : undefined) ??
    0;

  const mintedCount = walletSummary?.minted_tickets ?? 0;
  const listedCount = walletSummary?.listed_tickets ?? 0;

  const followingCount =
    overview?.following_count ??
    profile?.following_count ??
    0;

  const followerCount =
    overview?.follower_count ??
    profile?.follower_count ??
    0;

  return (
    <div>
      <PageHeader
        title="Dashboard"
        subtitle="Demo home for discovery, ticketing, rewards, and fan engagement."
        actions={
          <div className="row">
            <Link className="btn secondary" href="/events">
              Browse Events
            </Link>
            <Link className="btn ghost" href="/wallet">
              Open Wallet
            </Link>
          </div>
        }
      />

      {loading ? <div className="card">Loading dashboard...</div> : null}

      {error ? (
        <div className="card" style={{ border: '1px solid rgba(255,80,80,0.35)' }}>
          <div style={{ fontWeight: 700, marginBottom: 8 }}>Unable to load dashboard</div>
          <div style={{ opacity: 0.8 }}>{error}</div>
        </div>
      ) : null}

      {!loading ? (
        <>
          <div
            className="card"
            style={{
              marginBottom: 24,
              display: 'grid',
              gridTemplateColumns: '1.2fr 1fr',
              gap: 24,
              alignItems: 'center',
            }}
          >
            <div>
              <div style={{ fontSize: 36, fontWeight: 800, marginBottom: 10 }}>
                Welcome back, {displayName}
              </div>
              <div style={{ opacity: 0.76, lineHeight: 1.7, maxWidth: 760 }}>
                Backstage Pass combines event discovery, simulated ticketing, fan community,
                and reward-driven engagement in one prototype. Use this dashboard
                to jump into the core user flow quickly.
              </div>

              <div style={{ marginTop: 18, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                <Link className="btn" href="/events">
                  Discover Events
                </Link>
                <Link className="btn secondary" href="/rewards">
                  View Rewards
                </Link>
                <Link className="btn ghost" href="/profile">
                  Edit Profile
                </Link>
              </div>
            </div>

            <div
              style={{
                borderRadius: 24,
                background: 'rgba(255,255,255,0.04)',
                padding: 24,
                border: '1px solid rgba(255,255,255,0.08)',
              }}
            >
              <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 12 }}>
                Current profile snapshot
              </div>
              <div style={{ opacity: 0.76, lineHeight: 1.7 }}>
                <div>Email: {profile?.email || '—'}</div>
                <div>City: {profile?.city || '—'}</div>
                <div>
                  Preferred genres:{' '}
                  {profile?.preferred_genres?.length ? profile.preferred_genres.join(', ') : '—'}
                </div>
                <div>
                  Preferred artists:{' '}
                  {profile?.preferred_artists?.length ? profile.preferred_artists.join(', ') : '—'}
                </div>
                <div>Wallet-linked tickets: {ticketCount}</div>
                <div>Connected wallet: {walletSummary?.wallet_address || '—'}</div>
              </div>
            </div>
          </div>

          <div className="grid grid-3" style={{ marginBottom: 24 }}>
            <HeroStat label="Fan Points" value={fanPoints} hint="Current reward summary" />
            <HeroStat label="Tickets" value={ticketCount} hint="Wallet-linked ticket count" />
            <HeroStat label="Orders" value={orderCount} hint="Order activity snapshot" />
          </div>

          <div className="grid grid-3" style={{ marginBottom: 24 }}>
            <HeroStat label="Minted" value={mintedCount} hint="NFT-style minted tickets" />
            <HeroStat label="Listed" value={listedCount} hint="Currently active marketplace listings" />
            <HeroStat label="Following" value={followingCount} hint={`Followers: ${followerCount}`} />
          </div>

          <div className="grid grid-2">
            <div>
              <div style={{ fontSize: 22, fontWeight: 800, marginBottom: 14 }}>Recommended for you</div>
              <div style={{ display: 'grid', gap: 12 }}>
                {recommended.length > 0 ? (
                  recommended.map((event) => <EventMiniCard key={event.id} event={event} />)
                ) : (
                  <div className="card">No recommendation data available yet.</div>
                )}
              </div>
            </div>

            <div>
              <div style={{ fontSize: 22, fontWeight: 800, marginBottom: 14 }}>Nearby events</div>
              <div style={{ display: 'grid', gap: 12 }}>
                {nearby.length > 0 ? (
                  nearby.map((event) => <EventMiniCard key={event.id} event={event} />)
                ) : (
                  <div className="card">No nearby event data available yet.</div>
                )}
              </div>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}