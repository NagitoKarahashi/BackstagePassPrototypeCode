'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { usePrivy, useWallets } from '@privy-io/react-auth';
import { updateMyWalletAddress } from '@/lib/api/profiles';

function shortAddr(addr?: string | null) {
  if (!addr) return '';
  return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
}

type Props = {
  currentWalletAddress?: string | null;
  onConnected?: (address: string) => void;
};

export function ConnectWalletButton({
  currentWalletAddress,
  onConnected,
}: Props) {
  const { ready, authenticated, connectWallet } = usePrivy();
  const { wallets } = useWallets();

  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const lastSyncedRef = useRef<string>('');

  const address = useMemo(() => {
    if (!wallets || wallets.length === 0) return '';
    return wallets[0]?.address || '';
  }, [wallets]);

  useEffect(() => {
    lastSyncedRef.current = currentWalletAddress || '';
  }, [currentWalletAddress]);

  useEffect(() => {
    async function syncWallet() {
      if (!address) return;

      const normalizedCurrent = (currentWalletAddress || '').toLowerCase();
      const normalizedAddress = address.toLowerCase();
      const normalizedLastSynced = (lastSyncedRef.current || '').toLowerCase();

      if (
        normalizedAddress === normalizedCurrent ||
        normalizedAddress === normalizedLastSynced
      ) {
        return;
      }

      try {
        setSaving(true);
        setMessage('');
        await updateMyWalletAddress(address);
        lastSyncedRef.current = address;
        setMessage('Wallet connected and synced.');
        onConnected?.(address);
      } catch (e) {
        setMessage(e instanceof Error ? e.message : 'Failed to sync wallet');
      } finally {
        setSaving(false);
      }
    }

    void syncWallet();
  }, [address, currentWalletAddress, onConnected]);

  if (!ready) {
    return (
      <button className="btn ghost" disabled>
        Loading wallet...
      </button>
    );
  }

  return (
    <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
      {!address ? (
        <button className="btn" onClick={connectWallet} disabled={!authenticated}>
          Connect Wallet
        </button>
      ) : (
        <div className="badge">Wallet: {shortAddr(address)}</div>
      )}

      {saving ? <span className="muted small">Syncing...</span> : null}
      {message ? <span className="muted small">{message}</span> : null}
    </div>
  );
}