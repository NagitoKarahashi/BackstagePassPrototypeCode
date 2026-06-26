'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { PageHeader } from '@/components/common/PageHeader';
import { getMyNotifications } from '@/lib/api/notifications';

type NotificationItem = {
  id?: string;
  title?: string;
  message?: string;
  type?: string;
  artist_id?: string;
  artist_name?: string;
  event_id?: string;
  event_uuid?: string;
  created_at?: string;
  read?: boolean;
};

function normalizeNotifications(data: any): NotificationItem[] {
  if (Array.isArray(data)) return data;
  if (data && typeof data === 'object') {
    if (Array.isArray(data.items)) return data.items;
    if (Array.isArray(data.notifications)) return data.notifications;
    if (Array.isArray(data.data)) return data.data;
  }
  return [];
}

function formatDate(value?: string) {
  if (!value) return 'Unknown time';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString();
}

function buildTypeLabel(type?: string) {
  const normalized = (type || 'update').toLowerCase();

  if (normalized.includes('artist')) return 'Artist Update';
  if (normalized.includes('event')) return 'Event Alert';
  if (normalized.includes('reward')) return 'Reward Update';
  if (normalized.includes('chat')) return 'Chat Activity';

  return 'Notification';
}

function NotificationCard({ item }: { item: NotificationItem }) {
  const artistLink =
    item.artist_id ? `/artists/${encodeURIComponent(item.artist_id)}` : null;

  const eventLink =
    item.event_uuid
      ? `/events/${item.event_uuid}`
      : item.event_id
        ? `/events/${item.event_id}`
        : null;

  return (
    <div
      className="card"
      style={{
        border: item.read ? undefined : '1px solid rgba(66,184,131,0.22)',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'start',
          gap: 16,
          marginBottom: 12,
        }}
      >
        <div>
          <div style={{ fontSize: 13, opacity: 0.68, marginBottom: 6 }}>
            {buildTypeLabel(item.type)}
          </div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>
            {item.title || 'New platform update'}
          </div>
        </div>

        {!item.read ? (
          <span
            style={{
              padding: '6px 10px',
              borderRadius: 999,
              fontSize: 12,
              fontWeight: 700,
              background: 'rgba(66,184,131,0.18)',
              color: '#7CFFB2',
            }}
          >
            NEW
          </span>
        ) : null}
      </div>

      <div style={{ opacity: 0.78, lineHeight: 1.7, marginBottom: 14 }}>
        {item.message || 'No message content available.'}
      </div>

      <div style={{ fontSize: 13, opacity: 0.62, marginBottom: 14 }}>
        {formatDate(item.created_at)}
      </div>

      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
        {artistLink ? (
          <Link className="btn secondary" href={artistLink}>
            View Artist
          </Link>
        ) : null}

        {eventLink ? (
          <Link className="btn ghost" href={eventLink}>
            View Event
          </Link>
        ) : null}
      </div>
    </div>
  );
}

export default function NotificationsPage() {
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        setError('');

        const data = await getMyNotifications();
        const normalized = normalizeNotifications(data);
        setItems(normalized);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load notifications');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const unreadCount = useMemo(
    () => items.filter((item) => !item.read).length,
    [items]
  );

  return (
    <div>
      <PageHeader
        title="Notifications"
        subtitle="Artist and event updates connected to your current follow and engagement flows."
        actions={
          <div className="row">
            <Link className="btn secondary" href="/artists">
              Browse Artists
            </Link>
            <Link className="btn ghost" href="/artists/following">
              Following
            </Link>
          </div>
        }
      />

      {loading ? <div className="card">Loading notifications...</div> : null}

      {error ? (
        <div className="card" style={{ border: '1px solid rgba(255,80,80,0.35)' }}>
          <div style={{ fontWeight: 700, marginBottom: 8 }}>Unable to load notifications</div>
          <div style={{ opacity: 0.8 }}>{error}</div>
        </div>
      ) : null}

      <div className="grid grid-3" style={{ marginBottom: 24 }}>
        <div className="card">
          <div style={{ fontSize: 13, opacity: 0.7, marginBottom: 8 }}>Total Notifications</div>
          <div style={{ fontSize: 30, fontWeight: 800 }}>{items.length}</div>
        </div>
        <div className="card">
          <div style={{ fontSize: 13, opacity: 0.7, marginBottom: 8 }}>Unread</div>
          <div style={{ fontSize: 30, fontWeight: 800 }}>{unreadCount}</div>
        </div>
        <div className="card">
          <div style={{ fontSize: 13, opacity: 0.7, marginBottom: 8 }}>Prototype Scope</div>
          <div style={{ fontSize: 18, fontWeight: 700 }}>Artist / event updates</div>
        </div>
      </div>

      {items.length > 0 ? (
        <div className="grid" style={{ gap: 16 }}>
          {items.map((item, idx) => (
            <NotificationCard
              key={item.id || `${item.title || 'notification'}-${idx}`}
              item={item}
            />
          ))}
        </div>
      ) : !loading ? (
        <div className="card">
          <div style={{ fontSize: 20, fontWeight: 700, marginBottom: 10 }}>
            No notifications yet
          </div>
          <div style={{ opacity: 0.76, lineHeight: 1.7, marginBottom: 16 }}>
            Follow artists and interact with events to generate notification activity in this prototype.
          </div>

          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <Link className="btn" href="/artists">
              Explore Artists
            </Link>
            <Link className="btn secondary" href="/events">
              Browse Events
            </Link>
          </div>
        </div>
      ) : null}
    </div>
  );
}