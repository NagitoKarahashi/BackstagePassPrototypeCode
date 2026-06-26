'use client';

import Link from 'next/link';
import { usePrivy } from '@privy-io/react-auth';

export function TopNav({ statusMessage }: { statusMessage?: string }) {
  const { logout } = usePrivy();

  async function handleLogout() {
    try {
      await logout();
    } finally {
      window.location.href = '/login';
    }
  }

  return (
    <div className="topbar">
      <div className="muted small">{statusMessage || 'Phase 1 demo frontend'}</div>
      <div className="row">
        <Link href="/profile" className="btn secondary">
          Profile
        </Link>
        <button onClick={handleLogout} className="btn ghost">
          Logout
        </button>
      </div>
    </div>
  );
}