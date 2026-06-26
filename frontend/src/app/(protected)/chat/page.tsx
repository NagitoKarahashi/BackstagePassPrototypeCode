'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { PageHeader } from '@/components/common/PageHeader';
import { listMyChatRooms } from '@/lib/api/chat';

type ChatRoomItem = {
  room_id?: string;
  room_name?: string;
  room_type?: string;
  event_uuid?: string;
  event_id?: string;
  title?: string;
  artist?: string;
  city?: string;
  genre?: string;
  start_time?: string;
  poster_url?: string | null;
  ticket_status?: string;
};

function normalizeRooms(data: any): ChatRoomItem[] {
  if (Array.isArray(data)) return data;
  if (data && typeof data === 'object') {
    if (Array.isArray(data.items)) return data.items;
    if (Array.isArray(data.rooms)) return data.rooms;
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

function StatusBadge({ status }: { status?: string }) {
  const normalized = (status || 'unknown').toLowerCase();

  let bg = 'rgba(255,255,255,0.08)';
  let color = '#fff';

  if (normalized === 'active') {
    bg = 'rgba(66, 184, 131, 0.18)';
    color = '#7CFFB2';
  } else if (normalized === 'used') {
    bg = 'rgba(255, 184, 77, 0.18)';
    color = '#FFD27C';
  }

  return (
    <span
      style={{
        padding: '6px 10px',
        borderRadius: 999,
        fontSize: 12,
        fontWeight: 700,
        background: bg,
        color,
        textTransform: 'uppercase',
        letterSpacing: 0.4,
      }}
    >
      {normalized}
    </span>
  );
}

export default function ChatRoomsPage() {
  const [rooms, setRooms] = useState<ChatRoomItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        setError('');

        const data = await listMyChatRooms();
        setRooms(normalizeRooms(data));
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load chat rooms');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const activeCount = useMemo(
    () => rooms.filter((room) => (room.ticket_status || '').toLowerCase() === 'active').length,
    [rooms]
  );

  return (
    <div>
      <PageHeader
        title="Chat Rooms"
        subtitle="Event chat rooms currently available to this user based on eligible ticket access."
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

      {loading ? <div className="card">Loading chat rooms...</div> : null}

      {error ? (
        <div className="card" style={{ border: '1px solid rgba(255,80,80,0.35)' }}>
          <div style={{ fontWeight: 700, marginBottom: 8 }}>Unable to load chat rooms</div>
          <div style={{ opacity: 0.8 }}>{error}</div>
        </div>
      ) : null}

      <div className="grid grid-3" style={{ marginBottom: 24 }}>
        <div className="card">
          <div style={{ fontSize: 13, opacity: 0.7, marginBottom: 8 }}>Accessible Rooms</div>
          <div style={{ fontSize: 30, fontWeight: 800 }}>{rooms.length}</div>
        </div>
        <div className="card">
          <div style={{ fontSize: 13, opacity: 0.7, marginBottom: 8 }}>Active Ticket Rooms</div>
          <div style={{ fontSize: 30, fontWeight: 800 }}>{activeCount}</div>
        </div>
        <div className="card">
          <div style={{ fontSize: 13, opacity: 0.7, marginBottom: 8 }}>Access Logic</div>
          <div style={{ fontSize: 18, fontWeight: 700 }}>Ticket-based chat access</div>
        </div>
      </div>

      {rooms.length > 0 ? (
        <div className="grid grid-2">
          {rooms.map((room, idx) => {
            const eventUuid = room.event_uuid || room.event_id;
            const title = room.title || room.room_name || `Event Room ${idx + 1}`;

            return (
              <div className="card" key={room.room_id || eventUuid || idx}>
                <div
                  style={{
                    width: '100%',
                    height: 180,
                    borderRadius: 18,
                    overflow: 'hidden',
                    background: 'rgba(255,255,255,0.05)',
                    marginBottom: 16,
                    display: 'grid',
                    placeItems: 'center',
                  }}
                >
                  {room.poster_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={room.poster_url}
                      alt={title}
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    />
                  ) : (
                    <div style={{ opacity: 0.45, fontWeight: 700 }}>
                      {title}
                    </div>
                  )}
                </div>

                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'start',
                    gap: 16,
                    marginBottom: 10,
                  }}
                >
                  <div style={{ fontSize: 22, fontWeight: 800 }}>{title}</div>
                  <StatusBadge status={room.ticket_status} />
                </div>

                <div style={{ opacity: 0.76, lineHeight: 1.7, marginBottom: 14 }}>
                  <div><strong>Artist:</strong> {room.artist || '—'}</div>
                  <div><strong>City:</strong> {room.city || '—'}</div>
                  <div><strong>Genre:</strong> {room.genre || '—'}</div>
                  <div><strong>Start Time:</strong> {formatDate(room.start_time)}</div>
                </div>

                <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                  {eventUuid ? (
                    <Link className="btn" href={`/chat/${eventUuid}`}>
                      Open Chat
                    </Link>
                  ) : null}
                  {eventUuid ? (
                    <Link className="btn ghost" href={`/events/${eventUuid}`}>
                      Event Detail
                    </Link>
                  ) : null}
                </div>
              </div>
            );
          })}
        </div>
      ) : !loading ? (
        <div className="card">
          <div style={{ fontSize: 20, fontWeight: 700, marginBottom: 10 }}>
            No chat rooms available
          </div>
          <div style={{ opacity: 0.76, lineHeight: 1.7, marginBottom: 16 }}>
            Event chat rooms become available when your ticket status allows room access.
            Refunded and expired tickets should not grant chat access.
          </div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <Link className="btn" href="/events">
              Browse Events
            </Link>
            <Link className="btn secondary" href="/wallet">
              Check Wallet
            </Link>
          </div>
        </div>
      ) : null}
    </div>
  );
}