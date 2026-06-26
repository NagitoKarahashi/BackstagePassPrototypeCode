import Link from 'next/link';
import type { EventItem } from '@/lib/types';
import { formatDateTime } from '@/lib/utils/format';

export function EventCard({ event }: { event: EventItem }) {
  return (
    <Link href={`/events/${event.id}`} className="card" style={{ display: 'block' }}>
      {event.poster_url ? <img src={event.poster_url} alt={event.title} className="poster" /> : <div className="poster" />}
      <div className="space" />
      <div className="badge">{event.genre || 'Event'}</div>
      <h3>{event.title}</h3>
      <div className="muted small">{event.artist || 'Unknown artist'}</div>
      <div className="muted small">{event.city || 'Unknown city'} · {formatDateTime(event.starts_at || event.start_time)}</div>
      <div className="row" style={{ justifyContent: 'space-between', marginTop: 12 }}>
        <strong>{event.price ? `$${event.price}` : 'TBD'}</strong>
        <span className="small muted">{event.stock_left ?? '-'} left</span>
      </div>
    </Link>
  );
}
