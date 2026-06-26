'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'next/navigation';
import { PageHeader } from '@/components/common/PageHeader';
import { getMyProfile } from '@/lib/api/profiles';
import { getEventById } from '@/lib/api/events';
import { getEventChatRoom, getEventMessages, postEventMessage } from '@/lib/api/chat';

type EventLike = {
  id: string;
  title?: string;
  artist?: string;
  city?: string;
  genre?: string;
  description?: string;
  start_time?: string;
  poster_url?: string | null;
};

type RoomLike = {
  id?: string;
  event_uuid?: string;
  event_id?: string;
  room_name?: string;
  name?: string;
  title?: string;
};

type MessageItem = {
  id: string;
  user_id?: string;
  content?: string;
  created_at?: string;
  display_name?: string;
  username?: string;
  email?: string;
  sender_name?: string;
  raw?: unknown;
};

type ProfileLike = {
  id?: string | null;
  username?: string | null;
  display_name?: string | null;
  email?: string | null;
};

function stringifyUnknown(value: unknown): string {
  if (typeof value === 'string') return value;
  if (value == null) return '';
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

function pickFirstString(...values: unknown[]): string {
  for (const value of values) {
    if (typeof value === 'string' && value.trim()) return value;
    if (typeof value === 'number') return String(value);
  }
  return '';
}

function normalizeMessages(data: any): MessageItem[] {
  let raw: any[] = [];

  if (Array.isArray(data)) {
    raw = data;
  } else if (data && typeof data === 'object') {
    if (Array.isArray(data.items)) raw = data.items;
    else if (Array.isArray(data.messages)) raw = data.messages;
    else if (Array.isArray(data.data)) raw = data.data;
    else if (Array.isArray(data.results)) raw = data.results;
  }

  return raw.map((item: any, index: number) => {
    const userId = pickFirstString(
      item?.user_id,
      item?.sender_user_id,
      item?.sender_id,
      item?.author_id,
      item?.profile_id,
      item?.user?.id,
      item?.profile?.id
    );

    const textValue =
      item?.content ??
      item?.message ??
      item?.text ??
      item?.body ??
      item?.message_text ??
      item?.payload?.content ??
      item?.payload?.message ??
      item?.payload?.text ??
      item?.metadata?.content ??
      item?.metadata?.message;

    const content =
      typeof textValue === 'string'
        ? textValue
        : textValue != null
        ? stringifyUnknown(textValue)
        : '';

    const displayName = pickFirstString(
      item?.display_name,
      item?.sender_name,
      item?.name,
      item?.profile?.display_name,
      item?.user?.display_name,
      item?.user?.name
    );

    const username = pickFirstString(
      item?.username,
      item?.user_name,
      item?.sender_username,
      item?.profile?.username,
      item?.user?.username
    );

    const email = pickFirstString(
      item?.email,
      item?.user?.email,
      item?.profile?.email
    );

    return {
      id:
        pickFirstString(item?.id, item?.message_id, item?.chat_id, item?.uuid) ||
        `msg-${index}`,
      user_id: userId,
      content,
      created_at: pickFirstString(
        item?.created_at,
        item?.sent_at,
        item?.inserted_at,
        item?.timestamp
      ),
      display_name: displayName,
      username,
      email,
      sender_name: pickFirstString(item?.sender_name, displayName, username, email),
      raw: item,
    };
  });
}

function normalizeRoom(data: any): RoomLike | null {
  if (!data) return null;
  if (Array.isArray(data)) return data[0] || null;
  if (typeof data === 'object') {
    if (data.room) return data.room;
    return data;
  }
  return null;
}

function formatDate(value?: string) {
  if (!value) return '—';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString();
}

function MessageBubble({
  message,
  isMine,
  currentUserName,
}: {
  message: MessageItem;
  isMine: boolean;
  currentUserName?: string;
}) {
  const senderName = isMine
    ? currentUserName || 'You'
    : message.sender_name ||
      message.display_name ||
      message.username ||
      message.email ||
      (message.user_id ? `User ${String(message.user_id).slice(0, 8)}` : 'Unknown user');

  const content = message.content?.trim() || '(message content unavailable)';

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: isMine ? 'flex-end' : 'flex-start',
        marginBottom: 14,
      }}
    >
      <div
        style={{
          maxWidth: '72%',
          padding: '14px 16px',
          borderRadius: 18,
          background: isMine ? 'rgba(66,184,131,0.18)' : 'rgba(255,255,255,0.06)',
          border: '1px solid rgba(255,255,255,0.06)',
        }}
      >
        <div style={{ fontSize: 12, opacity: 0.65, marginBottom: 6 }}>{senderName}</div>
        <div style={{ lineHeight: 1.6, wordBreak: 'break-word', whiteSpace: 'pre-wrap' }}>
          {content}
        </div>
        <div style={{ fontSize: 11, opacity: 0.55, marginTop: 8 }}>
          {formatDate(message.created_at)}
        </div>
      </div>
    </div>
  );
}

export default function EventChatPage() {
  const params = useParams<{ eventUuid: string }>();
  const eventUuid = params.eventUuid;

  const [event, setEvent] = useState<EventLike | null>(null);
  const [room, setRoom] = useState<RoomLike | null>(null);
  const [backendEventId, setBackendEventId] = useState<string>('');
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [content, setContent] = useState('');
  const [profile, setProfile] = useState<ProfileLike | null>(null);

  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const [messageInfo, setMessageInfo] = useState('');

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        setError('');
        setMessageInfo('');

        if (!eventUuid) return;

        const [profileData, roomData, messagesData] = await Promise.all([
          getMyProfile().catch(() => null),
          getEventChatRoom(eventUuid),
          getEventMessages(eventUuid),
        ]);

        const normalizedRoom = normalizeRoom(roomData);
        const resolvedEventId =
          normalizedRoom?.event_id || normalizedRoom?.event_uuid || eventUuid;

        setProfile((profileData as ProfileLike | null) || null);
        setRoom(normalizedRoom);
        setBackendEventId(String(resolvedEventId));
        setMessages(normalizeMessages(messagesData));

        const eventData = await getEventById(String(resolvedEventId)).catch(() => null);
        setEvent((eventData as EventLike | null) || null);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load chat');
      } finally {
        setLoading(false);
      }
    })();
  }, [eventUuid]);

  const roomTitle = useMemo(() => {
    return event?.title || room?.room_name || room?.name || room?.title || 'Event Chat';
  }, [room, event]);

  const currentUserName = useMemo(() => {
    return profile?.display_name || profile?.username || profile?.email || 'You';
  }, [profile]);

  const currentInternalUserId = useMemo(() => {
    return profile?.id ? String(profile.id) : '';
  }, [profile]);

  async function refreshMessages() {
    try {
      if (!eventUuid) return;
      const data = await getEventMessages(eventUuid);
      setMessages(normalizeMessages(data));
    } catch (e) {
      console.error('refreshMessages failed:', e);
    }
  }

  async function handleSend() {
    try {
      setSending(true);
      setError('');
      setMessageInfo('');

      if (!eventUuid) throw new Error('Missing event id');
      if (!content.trim()) throw new Error('Message cannot be empty');

      await postEventMessage(eventUuid, {
        content: content.trim(),
      });

      setContent('');
      setMessageInfo('Message sent.');
      await refreshMessages();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to send message');
    } finally {
      setSending(false);
    }
  }

  if (loading) return <div className="card">Loading chat...</div>;

  return (
    <div>
      <PageHeader
        title={roomTitle}
        subtitle="Event-specific attendee chat room."
        actions={
          <div className="row">
            <Link href={`/events/${backendEventId || eventUuid}`} className="btn secondary">
              Back to Event
            </Link>
            <Link href="/risk" className="btn ghost">
              Risk Overview
            </Link>
            <button className="btn ghost" onClick={refreshMessages}>
              Refresh
            </button>
          </div>
        }
      />

      {error ? (
        <div className="card" style={{ border: '1px solid rgba(255,80,80,0.35)' }}>
          <div style={{ fontWeight: 700, marginBottom: 8 }}>Unable to use chat</div>
          <div style={{ opacity: 0.8, whiteSpace: 'pre-wrap' }}>{error}</div>
        </div>
      ) : null}

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '360px 1fr',
          gap: 24,
          alignItems: 'start',
        }}
      >
        <div style={{ display: 'grid', gap: 16 }}>
          <div className="card">
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
              {event?.poster_url ? (
                <img
                  src={event.poster_url}
                  alt={event?.title || 'Event poster'}
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
              ) : (
                <div style={{ opacity: 0.45, fontWeight: 700 }}>
                  {event?.title || 'Event'}
                </div>
              )}
            </div>

            <div style={{ fontSize: 22, fontWeight: 800, marginBottom: 8 }}>
              {event?.title || roomTitle}
            </div>
            <div style={{ opacity: 0.72, lineHeight: 1.6, marginBottom: 16 }}>
              {event?.description || 'No event description available yet.'}
            </div>

            <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 10 }}>Chat identity</div>
            <div className="small muted">Signed in as: {currentUserName}</div>
            <div className="small muted">Internal user ID: {currentInternalUserId || 'Unavailable'}</div>
          </div>
        </div>

        <div className="card">
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              gap: 16,
              marginBottom: 16,
            }}
          >
            <div>
              <div style={{ fontSize: 22, fontWeight: 800, marginBottom: 6 }}>Messages</div>
              <div style={{ opacity: 0.72 }}>Attendee discussion space for this event.</div>
            </div>

            <div style={{ opacity: 0.68, fontSize: 13 }}>
              {messages.length} message{messages.length === 1 ? '' : 's'}
            </div>
          </div>

          <div
            style={{
              minHeight: 420,
              maxHeight: 560,
              overflowY: 'auto',
              padding: 12,
              borderRadius: 16,
              background: 'rgba(255,255,255,0.03)',
              marginBottom: 16,
            }}
          >
            {messages.length > 0 ? (
              messages.map((msg) => (
                <MessageBubble
                  key={msg.id}
                  message={msg}
                  isMine={
                    !!currentInternalUserId &&
                    String(msg.user_id || '') === String(currentInternalUserId)
                  }
                  currentUserName={currentUserName}
                />
              ))
            ) : (
              <div style={{ opacity: 0.7 }}>
                No messages yet. Start the conversation with other attendees.
              </div>
            )}
          </div>

          {messageInfo ? (
            <div className="small" style={{ marginBottom: 12, opacity: 0.8 }}>
              {messageInfo}
            </div>
          ) : null}

          <div
            style={{
              display: 'grid',
              gap: 12,
              paddingBottom: 90,
            }}
          >
            <textarea
              className="textarea"
              rows={4}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Send a message to the event chat..."
            />
            <div className="row" style={{ justifyContent: 'flex-end', paddingRight: 220 }}>
              <button className="btn" onClick={handleSend} disabled={sending || !content.trim()}>
                {sending ? 'Sending...' : 'Send Message'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}