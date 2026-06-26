'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { PageHeader } from '@/components/common/PageHeader';
import { getFollowedArtists, unfollowArtist } from '@/lib/api/artists';

type FollowRecord = {
  artist_id?: string;
  id?: string;
};

function normalizeFollows(data: any): FollowRecord[] {
  if (Array.isArray(data)) return data;
  if (data && typeof data === 'object') {
    if (Array.isArray(data.items)) return data.items;
    if (Array.isArray(data.data)) return data.data;
  }
  return [];
}

export default function FollowingArtistsPage() {
  const [items, setItems] = useState<FollowRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busyId, setBusyId] = useState<string | null>(null);

  async function loadData() {
    try {
      setLoading(true);
      setError('');
      const data = await getFollowedArtists();
      setItems(normalizeFollows(data));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load following artists');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleUnfollow(artistId: string) {
    try {
      setBusyId(artistId);
      await unfollowArtist(artistId);
      await loadData();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to unfollow artist');
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div>
      <PageHeader
        title="Following Artists"
        subtitle="Artists you currently follow in the prototype."
        actions={
          <div className="row">
            <Link className="btn secondary" href="/artists">
              Browse Artists
            </Link>
            <Link className="btn ghost" href="/notifications">
              Notifications
            </Link>
          </div>
        }
      />

      {loading ? <div className="card">Loading following artists...</div> : null}

      {error ? (
        <div className="card" style={{ border: '1px solid rgba(255,80,80,0.35)' }}>
          <div style={{ fontWeight: 700, marginBottom: 8 }}>Unable to load following artists</div>
          <div style={{ opacity: 0.8 }}>{error}</div>
        </div>
      ) : null}

      <div className="grid grid-3" style={{ marginBottom: 24 }}>
        <div className="card">
          <div style={{ fontSize: 13, opacity: 0.7, marginBottom: 8 }}>Following Count</div>
          <div style={{ fontSize: 30, fontWeight: 800 }}>{items.length}</div>
        </div>
        <div className="card">
          <div style={{ fontSize: 13, opacity: 0.7, marginBottom: 8 }}>Notification Flow</div>
          <div style={{ fontSize: 18, fontWeight: 700 }}>Connected to artist updates</div>
        </div>
        <div className="card">
          <div style={{ fontSize: 13, opacity: 0.7, marginBottom: 8 }}>Prototype Scope</div>
          <div style={{ fontSize: 18, fontWeight: 700 }}>Follow / unfollow basics</div>
        </div>
      </div>

      {items.length > 0 ? (
        <div className="grid" style={{ gap: 16 }}>
          {items.map((item, idx) => {
            const artistId = item.artist_id || item.id || `artist-${idx}`;

            return (
              <div className="card" key={artistId}>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    gap: 16,
                    flexWrap: 'wrap',
                  }}
                >
                  <div>
                    <div style={{ fontSize: 22, fontWeight: 800, marginBottom: 8 }}>
                      {artistId}
                    </div>
                    <div style={{ opacity: 0.72 }}>
                      Currently followed in your artist network.
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                    <Link
                      className="btn secondary"
                      href={`/artists/${encodeURIComponent(artistId)}`}
                    >
                      View Artist
                    </Link>
                    <button
                      className="btn ghost"
                      onClick={() => handleUnfollow(artistId)}
                      disabled={busyId === artistId}
                    >
                      {busyId === artistId ? 'Updating...' : 'Unfollow'}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : !loading ? (
        <div className="card">
          <div style={{ fontSize: 20, fontWeight: 700, marginBottom: 10 }}>
            You are not following any artists yet
          </div>
          <div style={{ opacity: 0.76, lineHeight: 1.7, marginBottom: 16 }}>
            Browse the artist directory and follow artists to build your notification and engagement flow.
          </div>
          <Link className="btn" href="/artists">
            Explore Artists
          </Link>
        </div>
      ) : null}
    </div>
  );
}