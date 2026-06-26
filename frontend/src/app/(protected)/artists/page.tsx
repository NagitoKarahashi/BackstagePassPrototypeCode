'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { PageHeader } from '@/components/common/PageHeader';
import { listEvents } from '@/lib/api/events';
import { getFollowedArtists } from '@/lib/api/artists';

type EventItem = {
  id: string;
  artist?: string;
  city?: string;
  genre?: string;
  poster_url?: string | null;
};

type ArtistCardItem = {
  id: string;
  name: string;
  city?: string;
  genre?: string;
  poster_url?: string | null;
};

type FollowRecord = {
  artist_id?: string;
  id?: string;
};

function normalizeEvents(data: any): EventItem[] {
  if (Array.isArray(data)) return data;
  if (data && typeof data === 'object') {
    if (Array.isArray(data.items)) return data.items;
    if (Array.isArray(data.events)) return data.events;
    if (Array.isArray(data.data)) return data.data;
  }
  return [];
}

function normalizeFollows(data: any): FollowRecord[] {
  if (Array.isArray(data)) return data;
  if (data && typeof data === 'object') {
    if (Array.isArray(data.items)) return data.items;
    if (Array.isArray(data.data)) return data.data;
  }
  return [];
}

function buildArtistCards(events: EventItem[]): ArtistCardItem[] {
  const map = new Map<string, ArtistCardItem>();

  for (const event of events) {
    const artistName = (event.artist || '').trim();
    if (!artistName) continue;

    if (!map.has(artistName)) {
      map.set(artistName, {
        id: artistName,
        name: artistName,
        city: event.city,
        genre: event.genre,
        poster_url: event.poster_url || null,
      });
    }
  }

  return Array.from(map.values());
}

export default function ArtistsPage() {
  const [artists, setArtists] = useState<ArtistCardItem[]>([]);
  const [followedIds, setFollowedIds] = useState<string[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        setError('');

        const [eventsRes, followsRes] = await Promise.all([
          listEvents({ only_available: true, limit: 50 }).catch(() => ({ items: [] })),
          getFollowedArtists().catch(() => ({ items: [] })),
        ]);

        const eventItems = normalizeEvents(eventsRes);
        const followItems = normalizeFollows(followsRes);

        setArtists(buildArtistCards(eventItems));
        setFollowedIds(
          followItems
            .map((item) => item.artist_id || item.id)
            .filter(Boolean) as string[]
        );
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load artists');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const followedCount = useMemo(() => followedIds.length, [followedIds]);

  return (
    <div>
      <PageHeader
        title="Artists"
        subtitle="Browse artist / organizer profiles and open event-linked artist pages."
        actions={
          <div className="row">
            <Link className="btn secondary" href="/artists/following">
              Following
            </Link>
            <Link className="btn ghost" href="/notifications">
              Notifications
            </Link>
          </div>
        }
      />

      {loading ? <div className="card">Loading artists...</div> : null}

      {error ? (
        <div className="card" style={{ border: '1px solid rgba(255,80,80,0.35)' }}>
          <div style={{ fontWeight: 700, marginBottom: 8 }}>Unable to load artists</div>
          <div style={{ opacity: 0.8 }}>{error}</div>
        </div>
      ) : null}

      <div className="grid grid-3" style={{ marginBottom: 24 }}>
        <div className="card">
          <div style={{ fontSize: 13, opacity: 0.7, marginBottom: 8 }}>Artists Indexed</div>
          <div style={{ fontSize: 30, fontWeight: 800 }}>{artists.length}</div>
        </div>
        <div className="card">
          <div style={{ fontSize: 13, opacity: 0.7, marginBottom: 8 }}>Following</div>
          <div style={{ fontSize: 30, fontWeight: 800 }}>{followedCount}</div>
        </div>
        <div className="card">
          <div style={{ fontSize: 13, opacity: 0.7, marginBottom: 8 }}>Prototype Mode</div>
          <div style={{ fontSize: 18, fontWeight: 700 }}>Event-derived artist directory</div>
        </div>
      </div>

      {artists.length > 0 ? (
        <div className="grid grid-3">
          {artists.map((artist) => {
            const isFollowing = followedIds.includes(artist.id);

            return (
              <Link
                key={artist.id}
                href={`/artists/${encodeURIComponent(artist.id)}`}
                className="card"
                style={{
                  display: 'block',
                  textDecoration: 'none',
                  color: 'inherit',
                }}
              >
                <div
                  style={{
                    width: '100%',
                    height: 160,
                    borderRadius: 18,
                    overflow: 'hidden',
                    background: 'rgba(255,255,255,0.05)',
                    marginBottom: 14,
                    display: 'grid',
                    placeItems: 'center',
                  }}
                >
                  {artist.poster_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={artist.poster_url}
                      alt={artist.name}
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    />
                  ) : (
                    <div style={{ opacity: 0.45, fontWeight: 700 }}>{artist.name}</div>
                  )}
                </div>

                <div style={{ fontSize: 20, fontWeight: 800, marginBottom: 8 }}>
                  {artist.name}
                </div>
                <div style={{ opacity: 0.72, marginBottom: 6 }}>
                  {artist.city || 'City TBD'} {artist.genre ? `· ${artist.genre}` : ''}
                </div>
                <div style={{ opacity: 0.72 }}>
                  {isFollowing ? 'Following' : 'Open Artist Page'}
                </div>
              </Link>
            );
          })}
        </div>
      ) : !loading ? (
        <div className="card" style={{ opacity: 0.75 }}>
          No artist profiles are available yet. Once events are loaded, artists can be derived from event data and shown here.
        </div>
      ) : null}
    </div>
  );
}