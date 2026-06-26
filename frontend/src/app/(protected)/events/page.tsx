'use client';

import { useEffect, useState } from 'react';
import { PageHeader } from '@/components/common/PageHeader';
import { EventFilters } from '@/components/events/EventFilters';
import { EventCard } from '@/components/events/EventCard';
import { listEvents } from '@/lib/api/events';
import type { EventItem } from '@/lib/types';

export default function EventsPage() {
  const [filters, setFilters] = useState({ q: '', city: '', genre: '' });
  const [items, setItems] = useState<EventItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listEvents({ ...filters, only_available: true }).then((res) => setItems(res.items)).catch((e) => setError(e.message));
  }, [filters]);

  return (
    <div>
      <PageHeader title="Events" subtitle="Real API page: list, filter, and open event detail." />
      <EventFilters q={filters.q} city={filters.city} genre={filters.genre} onChange={(key, value) => setFilters((prev) => ({ ...prev, [key]: value }))} />
      <div className="space" />
      {error ? <div className="card">{error}</div> : null}
      <div className="grid grid-3">
        {items.map((event) => <EventCard key={event.id} event={event} />)}
      </div>
    </div>
  );
}
