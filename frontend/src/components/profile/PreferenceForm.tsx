'use client';

import { useState } from 'react';
import type { Profile } from '@/lib/types';

export function PreferenceForm({ profile, onSave }: { profile: Profile; onSave: (payload: Partial<Profile>) => Promise<void> }) {
  const [displayName, setDisplayName] = useState(profile.display_name || '');
  const [username, setUsername] = useState(profile.username || '');
  const [city, setCity] = useState(profile.city || '');
  const [bio, setBio] = useState(profile.bio || '');
  const [genres, setGenres] = useState((profile.preferred_genres || []).join(', '));
  const [artists, setArtists] = useState((profile.preferred_artists || []).join(', '));

  return (
    <div className="card">
      <h3>Edit profile</h3>
      <div className="grid grid-2">
        <input className="input" value={displayName} onChange={(e) => setDisplayName(e.target.value)} placeholder="Display name" />
        <input className="input" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Username" />
      </div>
      <div className="space" />
      <input className="input" value={city} onChange={(e) => setCity(e.target.value)} placeholder="City" />
      <div className="space" />
      <textarea className="textarea" rows={4} value={bio} onChange={(e) => setBio(e.target.value)} placeholder="Bio" />
      <div className="space" />
      <input className="input" value={genres} onChange={(e) => setGenres(e.target.value)} placeholder="Preferred genres, comma-separated" />
      <div className="space" />
      <input className="input" value={artists} onChange={(e) => setArtists(e.target.value)} placeholder="Preferred artists, comma-separated" />
      <div className="space" />
      <button
        className="btn"
        onClick={() => onSave({
          display_name: displayName,
          username,
          city,
          bio,
          preferred_genres: genres.split(',').map((v) => v.trim()).filter(Boolean),
          preferred_artists: artists.split(',').map((v) => v.trim()).filter(Boolean),
        })}
      >
        Save changes
      </button>
    </div>
  );
}
