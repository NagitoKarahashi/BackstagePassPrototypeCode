'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { usePrivy } from '@privy-io/react-auth';
import { AppSidebar } from './AppSidebar';
import { TopNav } from './TopNav';
import AskPanel from '@/components/ask/AskPanel';
import { bootstrapProfile } from '@/lib/auth/bootstrap';
import { setPrivyAccessTokenGetter } from '@/lib/auth/privy-token';

function getMissingEnv(): string[] {
  const missing: string[] = [];
  if (!process.env.NEXT_PUBLIC_API_BASE_URL) missing.push('NEXT_PUBLIC_API_BASE_URL');
  if (!process.env.NEXT_PUBLIC_PRIVY_APP_ID) missing.push('NEXT_PUBLIC_PRIVY_APP_ID');
  return missing;
}

async function sleep(ms: number) {
  await new Promise((resolve) => setTimeout(resolve, ms));
}

export function ProtectedShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { ready, authenticated, user, getAccessToken } = usePrivy();

  const [shellReady, setShellReady] = useState(false);
  const [message, setMessage] = useState('Checking session...');
  const missingEnv = useMemo(() => getMissingEnv(), []);

  useEffect(() => {
    // 再保险一次：把 Privy token getter 在这里也注册好
    setPrivyAccessTokenGetter(async () => {
      const token = await getAccessToken();
      return token ?? null;
    });
  }, [getAccessToken]);

  useEffect(() => {
    let alive = true;

    async function init() {
      if (missingEnv.length > 0) {
        setShellReady(false);
        return;
      }

      if (!ready) {
        setMessage('Preparing authentication...');
        return;
      }

      if (!authenticated) {
        router.replace('/login');
        return;
      }

      try {
        setMessage('Preparing Privy token...');

        let token: string | null = null;

        // 给 Privy token 一点初始化时间，避免 authenticated=true 但 token getter 还没就绪
        for (let i = 0; i < 5; i++) {
          token = (await getAccessToken()) ?? null;
          if (token) break;
          await sleep(300);
        }

        if (!token) {
          if (!alive) return;
          setMessage('Session OK. Bootstrap note: Privy token not ready yet.');
          setShellReady(true);
          return;
        }

        setMessage('Bootstrapping profile...');
        await bootstrapProfile();

        if (!alive) return;
        setMessage('Session OK');
      } catch (err) {
        if (!alive) return;
        const msg = err instanceof Error ? err.message : 'Profile bootstrap skipped';
        setMessage(`Session OK. Bootstrap note: ${msg}`);
      }

      if (!alive) return;
      setShellReady(true);
    }

    init();

    return () => {
      alive = false;
    };
  }, [missingEnv, ready, authenticated, router, getAccessToken]);

  if (missingEnv.length > 0) {
    return (
      <main className="page" style={{ minHeight: '100vh', display: 'grid', placeItems: 'center' }}>
        <div className="card" style={{ width: '100%', maxWidth: 760 }}>
          <div className="badge">Setup required</div>
          <h1>Missing frontend environment variables</h1>
          <p className="muted">
            Configure the required values in Vercel or <code>.env.local</code>, then redeploy / restart.
          </p>
          <pre className="small muted" style={{ whiteSpace: 'pre-wrap' }}>
{`NEXT_PUBLIC_API_BASE_URL=https://backstagepasscodebytan.onrender.com/api/v1
NEXT_PUBLIC_PRIVY_APP_ID=your_privy_app_id`}
          </pre>
          <div className="space" />
          <div className="small">Missing now: {missingEnv.join(', ')}</div>
        </div>
      </main>
    );
  }

  if (!ready || !shellReady) {
    return (
      <main className="page" style={{ minHeight: '100vh', display: 'grid', placeItems: 'center' }}>
        <div className="card" style={{ width: '100%', maxWidth: 640 }}>
          <div className="badge">Backstage Pass</div>
          <h1>Preparing your session</h1>
          <div className="muted small">{message}</div>
          <div className="space" />
          <div className="muted small">
            Ready: {String(ready)} · Authenticated: {String(authenticated)}
          </div>
          <div className="muted small">
            User: {user?.email?.address || user?.id || 'Not signed in'}
          </div>
        </div>
      </main>
    );
  }

  return (
    <div className="sidebar-layout">
      <AppSidebar />
      <main className="main-area">
        <TopNav statusMessage={message} />
        {children}
        <AskPanel />
      </main>
    </div>
  );
} 