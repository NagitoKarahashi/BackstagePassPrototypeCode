'use client';

import { useState } from 'react';

export function FollowButton({ initialFollowing = false, onToggle }: { initialFollowing?: boolean; onToggle: (next: boolean) => Promise<void> }) {
  const [following, setFollowing] = useState(initialFollowing);
  const [loading, setLoading] = useState(false);

  async function toggle() {
    setLoading(true);
    try {
      const next = !following;
      await onToggle(next);
      setFollowing(next);
    } finally {
      setLoading(false);
    }
  }

  return <button className="btn" onClick={toggle} disabled={loading}>{loading ? 'Working...' : following ? 'Following' : 'Follow artist'}</button>;
}
