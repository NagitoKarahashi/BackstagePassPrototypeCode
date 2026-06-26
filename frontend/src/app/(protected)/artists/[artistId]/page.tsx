'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'next/navigation';
import { PageHeader } from '@/components/common/PageHeader';
import { followArtist, getFollowedArtists, unfollowArtist } from '@/lib/api/artists';
import { listEvents } from '@/lib/api/events';

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

function formatDate(value?: string | null) {
  if (!value) return 'TBD';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString();
}

function InfoStat({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {
  return (
    <div className="card">
      <div style={{ fontSize: 13, opacity: 0.7, marginBottom: 8 }}>{label}</div>
      <div style={{ fontSize: 28, fontWeight: 800 }}>{value}</div>
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
          background: 'rgba(255,255,255,0.05)',
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
          <div style={{ opacity: 0.45, fontWeight: 700 }}>
            {event.title || 'Event'}
          </div>
        )}
      </div>

      <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>
        {event.title || 'Untitled event'}
      </div>
      <div style={{ opacity: 0.72, marginBottom: 6 }}>
        {event.city || 'Unknown city'} · {event.genre || 'Genre TBD'}
      </div>
      <div style={{ opacity: 0.72, marginBottom: 6 }}>
        {formatDate(event.start_time)}
      </div>
      <div style={{ opacity: 0.72 }}>
        {event.price ? `$${event.price}` : 'TBD'}{' '}
        {typeof event.stock_left === 'number' ? `· ${event.stock_left} left` : ''}
      </div>
    </Link>
  );
}

export default function ArtistDetailPage() {
  const params = useParams<{ artistId: string }>();

  const rawArtistId = params.artistId || '';
  const artistId = decodeURIComponent(rawArtistId);

  const [events, setEvents] = useState<EventItem[]>([]);
  const [isFollowing, setIsFollowing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [followLoading, setFollowLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        setError('');
        setMessage('');

        const [eventsRes, followsRes] = await Promise.all([
          listEvents({ artist: artistId, limit: 12 }).catch(() => ({ items: [] })),
          getFollowedArtists().catch(() => ({ items: [] })),
        ]);

        const eventItems = normalizeEvents(eventsRes);
        const followItems = normalizeFollows(followsRes);

        setEvents(eventItems);
        setIsFollowing(
          followItems.some((item) => item.artist_id === artistId || item.id === artistId)
        );
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load artist page');
      } finally {
        setLoading(false);
      }
    })();
  }, [artistId]);

  const artistName = useMemo(() => {
    return events[0]?.artist || artistId || 'Artist';
  }, [events, artistId]);

  const upcomingCount = events.length;
  const cityCount = new Set(events.map((e) => e.city).filter(Boolean)).size;
  const genreCount = new Set(events.map((e) => e.genre).filter(Boolean)).size;

  async function toggleFollow() {
    try {
      setFollowLoading(true);
      setError('');
      setMessage('');

      if (isFollowing) {
        await unfollowArtist(artistId);
        setIsFollowing(false);
        setMessage(`Unfollowed ${artistName}.`);
      } else {
        await followArtist(artistId);
        setIsFollowing(true);
        setMessage(`Now following ${artistName}.`);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to update follow status');
    } finally {
      setFollowLoading(false);
    }
  }

  if (loading) {
    return <div className="card">Loading artist page...</div>;
  }

  return (
    <div>
      <PageHeader
        title={artistName}
        subtitle="Artist / organizer page for event discovery and follow actions."
        actions={
          <div className="row">
            <button className="btn" onClick={toggleFollow} disabled={followLoading}>
              {followLoading
                ? 'Updating...'
                : isFollowing
                  ? 'Unfollow Artist'
                  : 'Follow Artist'}
            </button>
            <Link className="btn secondary" href="/notifications">
              Notifications
            </Link>
          </div>
        }
      />

      {error ? (
        <div className="card" style={{ border: '1px solid rgba(255,80,80,0.35)' }}>
          <div style={{ fontWeight: 700, marginBottom: 8 }}>Unable to load artist page</div>
          <div style={{ opacity: 0.8 }}>{error}</div>
        </div>
      ) : null}

      {message ? (
        <div className="card" style={{ border: '1px solid rgba(66,184,131,0.25)' }}>
          <div style={{ color: '#8fd19e' }}>{message}</div>
        </div>
      ) : null}

      <div
        className="card"
        style={{
          marginBottom: 24,
          display: 'grid',
          gridTemplateColumns: '1.1fr 1fr',
          gap: 24,
          alignItems: 'center',
        }}
      >
        <div>
          <div style={{ fontSize: 34, fontWeight: 800, marginBottom: 10 }}>
            {artistName}
          </div>
          <div style={{ opacity: 0.76, lineHeight: 1.8, maxWidth: 780 }}>
            {artistName} is presented here as an artist / organizer profile in the Phase 1 prototype.
            This page combines follow behavior with event-driven discovery, using current event data
            and lightweight profile presentation before a full artist CMS is introduced.
          </div>

          <div style={{ marginTop: 18, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <button className="btn" onClick={toggleFollow} disabled={followLoading}>
              {followLoading
                ? 'Updating...'
                : isFollowing
                  ? 'Unfollow Artist'
                  : 'Follow Artist'}
            </button>
            <Link className="btn ghost" href="/artists/following">
              My Following
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
            Artist Snapshot
          </div>
          <div style={{ opacity: 0.76, lineHeight: 1.8 }}>
            <div>Name: {artistName}</div>
            <div>Followed: {isFollowing ? 'Yes' : 'No'}</div>
            <div>Upcoming events: {upcomingCount}</div>
            <div>Active cities: {cityCount}</div>
            <div>Genres represented: {genreCount}</div>
          </div>
        </div>
      </div>

      <div className="grid grid-3" style={{ marginBottom: 24 }}>
        <InfoStat label="Upcoming Events" value={upcomingCount} />
        <InfoStat label="Cities" value={cityCount} />
        <InfoStat label="Genre Spread" value={genreCount} />
      </div>

      <div className="grid grid-2" style={{ marginBottom: 24, alignItems: 'start' }}>
        <div className="card">
          <div style={{ fontSize: 22, fontWeight: 800, marginBottom: 12 }}>Biography</div>
          <div style={{ opacity: 0.76, lineHeight: 1.8 }}>
            This biography section is currently a presentation block for the prototype. In Phase 1,
            it helps demonstrate the intended artist/organizer experience before a richer content
            management flow is introduced.
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: 22, fontWeight: 800, marginBottom: 12 }}>Engagement Notes</div>
          <div style={{ opacity: 0.76, lineHeight: 1.8 }}>
            Fans can follow artists, check upcoming shows, and move into event discovery and ticketing flows.
            This page is designed to connect artist visibility with notifications and future loyalty mechanics.
          </div>
        </div>
      </div>

      <div className="card">
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'start',
            gap: 16,
            marginBottom: 16,
          }}
        >
          <div>
            <div style={{ fontSize: 22, fontWeight: 800, marginBottom: 6 }}>Upcoming Events</div>
            <div style={{ opacity: 0.72, lineHeight: 1.5 }}>
              Event list currently derived from the event discovery backend using artist filtering.
            </div>
          </div>
          <Link className="btn ghost" href="/events">
            Browse All Events
          </Link>
        </div>

        {events.length > 0 ? (
          <div className="grid grid-3">
            {events.map((event) => (
              <EventMiniCard key={event.id} event={event} />
            ))}
          </div>
        ) : (
          <div style={{ opacity: 0.72 }}>
            No upcoming events found for this artist yet.
          </div>
        )}
      </div>
    </div>
  );
}