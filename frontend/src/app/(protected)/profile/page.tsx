'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { PageHeader } from '@/components/common/PageHeader';
import { getMyProfile } from '@/lib/api/profiles';
import { getMeHistory } from '@/lib/api/me';
import { ConnectWalletButton } from '@/components/web3/ConnectWalletButton';

type Profile = {
  id: string;
  display_name?: string | null;
  username?: string | null;
  email?: string | null;
  avatar_url?: string | null;
  bio?: string | null;
  city?: string | null;
  wallet_address?: string | null;
  preferred_genres?: string[];
  preferred_artists?: string[];
  fan_points?: number;
  following_count?: number;
  follower_count?: number;
  created_at?: string | null;
  last_active_at?: string | null;
};

type HistoryResponse = {
  orders?: unknown[];
  tickets?: unknown[];
};

function InfoRow({
  label,
  value,
}: {
  label: string;
  value?: string | number | null;
}) {
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ fontSize: 13, opacity: 0.65, marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 15, fontWeight: 500 }}>
        {value !== null && value !== undefined && value !== '' ? value : '—'}
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {
  return (
    <div className="card">
      <div style={{ fontSize: 13, opacity: 0.7, marginBottom: 8 }}>{label}</div>
      <div style={{ fontSize: 28, fontWeight: 700 }}>{value}</div>
    </div>
  );
}

function TagList({
  title,
  items,
  emptyText,
}: {
  title: string;
  items?: string[];
  emptyText: string;
}) {
  return (
    <div className="card">
      <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 14 }}>{title}</div>

      {items && items.length > 0 ? (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
          {items.map((item) => (
            <span
              key={item}
              style={{
                padding: '8px 12px',
                borderRadius: 999,
                background: 'rgba(255,255,255,0.08)',
                fontSize: 14,
                fontWeight: 500,
              }}
            >
              {item}
            </span>
          ))}
        </div>
      ) : (
        <div style={{ opacity: 0.72 }}>{emptyText}</div>
      )}
    </div>
  );
}

function HistoryCard({
  title,
  count,
  description,
}: {
  title: string;
  count: number;
  description: string;
}) {
  return (
    <div className="card">
      <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>{title}</div>
      <div style={{ fontSize: 32, fontWeight: 800, marginBottom: 8 }}>{count}</div>
      <div style={{ opacity: 0.72, lineHeight: 1.6 }}>{description}</div>
    </div>
  );
}

function formatDate(value?: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function buildDisplayName(profile?: Profile | null) {
  if (!profile) return 'User';

  const candidates = [
    profile.display_name,
    profile.username,
    profile.email,
  ].filter(Boolean) as string[];

  const cleaned = candidates.find((v) => !v.startsWith('did:privy:'));
  return cleaned || 'User';
}

export default function ProfilePage() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [history, setHistory] = useState<HistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        setError('');

        const [profileData, historyData] = await Promise.all([
          getMyProfile(),
          getMeHistory().catch(() => null),
        ]);

        setProfile(profileData as Profile);
        setHistory((historyData || null) as HistoryResponse | null);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load profile');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const displayName = useMemo(() => buildDisplayName(profile), [profile]);
  const orderCount = Array.isArray(history?.orders) ? history.orders.length : 0;
  const ticketCount = Array.isArray(history?.tickets) ? history.tickets.length : 0;

  return (
    <div>
      <PageHeader
        title="My Profile"
        subtitle="Current-user profile, preferences, wallet connection, and engagement overview."
        actions={
          <Link className="btn" href="/profile/edit">
            Edit Profile
          </Link>
        }
      />

      {loading ? <div className="card">Loading profile...</div> : null}

      {error ? (
        <div className="card" style={{ border: '1px solid rgba(255,80,80,0.35)' }}>
          <div style={{ fontWeight: 700, marginBottom: 8 }}>Unable to load profile</div>
          <div style={{ opacity: 0.8 }}>{error}</div>
        </div>
      ) : null}

      {profile ? (
        <>
          <div
            className="card"
            style={{
              display: 'grid',
              gridTemplateColumns: '120px 1fr',
              gap: 24,
              alignItems: 'center',
              marginBottom: 24,
            }}
          >
            <div
              style={{
                width: 120,
                height: 120,
                borderRadius: '50%',
                display: 'grid',
                placeItems: 'center',
                fontSize: 36,
                fontWeight: 700,
                background: 'rgba(255,255,255,0.08)',
                overflow: 'hidden',
              }}
            >
              {profile.avatar_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={profile.avatar_url}
                  alt={displayName}
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
              ) : (
                (displayName?.[0] || 'U').toUpperCase()
              )}
            </div>

            <div>
              <div style={{ fontSize: 32, fontWeight: 800, marginBottom: 8 }}>
                {displayName}
              </div>

              <div style={{ opacity: 0.75, marginBottom: 12 }}>
                {profile.email || 'No email available'}
              </div>

              <div style={{ opacity: 0.85, lineHeight: 1.7 }}>
                {profile.bio || 'No bio added yet. You can update your profile details from the edit page.'}
              </div>
            </div>
          </div>

          <div className="grid grid-4" style={{ marginBottom: 24 }}>
            <StatCard label="Fan Points" value={profile.fan_points ?? 0} />
            <StatCard label="Following" value={profile.following_count ?? 0} />
            <StatCard label="Followers" value={profile.follower_count ?? 0} />
            <StatCard label="Tickets" value={ticketCount} />
          </div>

          <div className="card" style={{ marginBottom: 24 }}>
            <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 12 }}>Web3 Wallet</div>
            <div style={{ opacity: 0.78, lineHeight: 1.7, marginBottom: 12 }}>
              Connect a wallet to prepare for NFT ticket ownership, collectible passes,
              and future on-chain transfer flows.
            </div>

            <div style={{ marginBottom: 12 }}>
              <div style={{ fontSize: 13, opacity: 0.65, marginBottom: 4 }}>Current Wallet</div>
              <div style={{ fontSize: 15, fontWeight: 500 }}>
                {profile.wallet_address || 'Not connected'}
              </div>
            </div>

            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              <ConnectWalletButton
                currentWalletAddress={profile.wallet_address}
                onConnected={() => {
                  void getMyProfile()
                    .then((data) => setProfile(data as Profile))
                    .catch(() => {});
                }}
              />
              <Link href="/wallet" className="btn ghost">
                Open Wallet
              </Link>
              <Link href="/market" className="btn ghost">
                Open Marketplace
              </Link>
            </div>
          </div>

          <div className="grid grid-2" style={{ marginBottom: 24 }}>
            <div className="card">
              <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 16 }}>
                Account Details
              </div>

              <InfoRow label="Display Name" value={profile.display_name} />
              <InfoRow label="Username" value={profile.username} />
              <InfoRow label="City" value={profile.city} />
              <InfoRow label="Wallet Address" value={profile.wallet_address} />
              <InfoRow label="Joined At" value={formatDate(profile.created_at)} />
              <InfoRow label="Last Active" value={formatDate(profile.last_active_at)} />
            </div>

            <div className="grid" style={{ gap: 16 }}>
              <HistoryCard
                title="Order History"
                count={orderCount}
                description="Number of orders currently returned from the current-user history endpoint."
              />
              <HistoryCard
                title="Ticket History"
                count={ticketCount}
                description="Tickets currently linked to this user in the backend history response."
              />
            </div>
          </div>

          <div className="grid grid-2">
            <TagList
              title="Preferred Genres"
              items={profile.preferred_genres}
              emptyText="No preferred genres selected yet."
            />
            <TagList
              title="Preferred Artists"
              items={profile.preferred_artists}
              emptyText="No preferred artists selected yet."
            />
          </div>
        </>
      ) : null}
    </div>
  );
}