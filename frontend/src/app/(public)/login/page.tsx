'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { usePrivy } from '@privy-io/react-auth';

export default function LoginPage() {
  const router = useRouter();
  const [message, setMessage] = useState('Use Privy login to continue.');
  const [forceLoginPage, setForceLoginPage] = useState(false);

  const { ready, authenticated, login, logout, user } = usePrivy();

  const missingEnv = useMemo(() => {
    const missing: string[] = [];
    if (!process.env.NEXT_PUBLIC_API_BASE_URL) missing.push('NEXT_PUBLIC_API_BASE_URL');
    if (!process.env.NEXT_PUBLIC_PRIVY_APP_ID) missing.push('NEXT_PUBLIC_PRIVY_APP_ID');
    return missing;
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const params = new URLSearchParams(window.location.search);
    setForceLoginPage(params.get('forceLogin') === '1');
  }, []);

  useEffect(() => {
    console.log('Login page state:', { ready, authenticated, forceLoginPage, user });

    if (!ready) return;
    if (authenticated && !forceLoginPage) {
      router.replace('/dashboard');
    }
  }, [ready, authenticated, forceLoginPage, router, user]);

  async function handleContinue() {
    try {
      console.log('Continue clicked');

      if (authenticated) {
        router.push('/dashboard');
        return;
      }

      setMessage('Opening Privy login...');
      await login();
    } catch (error) {
      console.error('Privy login failed:', error);
      setMessage(error instanceof Error ? error.message : 'Privy login failed');
    }
  }

  async function handleLogout() {
    try {
      console.log('Logout clicked');
      await logout();
      setMessage('Logged out. You can sign in again.');
    } catch (error) {
      console.error('Privy logout failed:', error);
      setMessage(error instanceof Error ? error.message : 'Privy logout failed');
    }
  }

  return (
    <div className="page" style={{ minHeight: '100vh', display: 'grid', placeItems: 'center' }}>
      <div className="card" style={{ width: '100%', maxWidth: 520 }}>
        <div className="badge">Backstage Pass · Phase 2</div>
        <h1>Login</h1>
        <p className="muted">
          Use Privy authentication to continue.
        </p>

        {missingEnv.length > 0 ? (
          <>
            <div className="space" />
            <div className="card" style={{ background: 'rgba(255,255,255,0.04)' }}>
              <div><strong>Missing environment values</strong></div>
              <div className="small muted">{missingEnv.join(', ')}</div>
            </div>
          </>
        ) : null}

        <div className="space" />
        <button className="btn" onClick={handleContinue} disabled={!ready || missingEnv.length > 0}>
          {authenticated ? 'Go to Dashboard' : 'Continue'}
        </button>

        <div className="space" />
        <button className="btn ghost" onClick={handleLogout} disabled={!ready}>
          Logout
        </button>

        <div className="space" />
        <div className="muted small">{message}</div>

        <div className="space" />
        <div className="muted small">
          Ready: {String(ready)} · Authenticated: {String(authenticated)} · Force login page: {String(forceLoginPage)}
        </div>
        <div className="muted small">
          User: {user?.email?.address || user?.id || 'Not signed in'}
        </div>
      </div>
    </div>
  );
}