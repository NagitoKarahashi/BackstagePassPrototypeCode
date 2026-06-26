'use client';

export function EventFilters({
  q,
  city,
  genre,
  onChange,
}: {
  q: string;
  city: string;
  genre: string;
  onChange: (key: string, value: string) => void;
}) {
  return (
    <div className="card row">
      <input className="input" placeholder="Search events" value={q} onChange={(e) => onChange('q', e.target.value)} />
      <input className="input" placeholder="City" value={city} onChange={(e) => onChange('city', e.target.value)} />
      <input className="input" placeholder="Genre" value={genre} onChange={(e) => onChange('genre', e.target.value)} />
    </div>
  );
}
