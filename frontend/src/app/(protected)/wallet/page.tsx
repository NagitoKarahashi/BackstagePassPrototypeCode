'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { useWallets } from '@privy-io/react-auth';
import { PageHeader } from '@/components/common/PageHeader';
import { getWalletMe, getWalletTickets } from '@/lib/api/wallet';
import { mintTicket } from '@/lib/api/web3';

type WalletMe = {
  wallet_address?: string | null;
  total_tickets?: number;
  minted_tickets?: number;
  listed_tickets?: number;
};

type WalletTicket = {
  id: string;
  event_id?: string | null;
  event_uuid?: string | null;
  order_id?: string | null;
  title?: string | null;
  artist?: string | null;
  city?: string | null;
  genre?: string | null;
  start_time?: string | null;
  poster_url?: string | null;
  token_id?: string | null;
  contract_address?: string | null;
  chain?: string | null;
  qr_payload?: string | null;
  status?: string | null;
  created_at?: string | null;
  metadata?: Record<string, unknown> | null;
  metadata_uri?: string | null;
  owner_wallet?: string | null;
  mint_status?: string | null;
  minted_at?: string | null;
  tx_hash?: string | null;
  is_listed?: boolean;
};

function normalizeTickets(data: unknown): WalletTicket[] {
  if (Array.isArray(data)) return data as WalletTicket[];

  if (data && typeof data === 'object') {
    const obj = data as Record<string, unknown>;

    if (Array.isArray(obj.items)) return obj.items as WalletTicket[];
    if (Array.isArray(obj.tickets)) return obj.tickets as WalletTicket[];
    if (Array.isArray(obj.data)) return obj.data as WalletTicket[];
  }

  return [];
}

function shortAddr(value?: string | null) {
  if (!value) return '—';
  if (value.length <= 18) return value;
  return `${value.slice(0, 8)}...${value.slice(-6)}`;
}

function StatusBadge({ status }: { status?: string | null }) {
  const normalized = (status || 'unknown').toLowerCase();

  let bg = 'rgba(255,255,255,0.08)';
  let color = '#fff';

  if (normalized === 'active') {
    bg = 'rgba(66, 184, 131, 0.18)';
    color = '#7CFFB2';
  } else if (normalized === 'used') {
    bg = 'rgba(255, 184, 77, 0.18)';
    color = '#FFD27C';
  } else if (normalized === 'expired') {
    bg = 'rgba(255, 99, 99, 0.18)';
    color = '#FF9A9A';
  } else if (normalized === 'refunded') {
    bg = 'rgba(160, 160, 160, 0.18)';
    color = '#D8D8D8';
  }

  return (
    <span
      style={{
        padding: '6px 10px',
        borderRadius: 999,
        fontSize: 12,
        fontWeight: 700,
        background: bg,
        color,
        textTransform: 'uppercase',
        letterSpacing: 0.4,
      }}
    >
      {normalized}
    </span>
  );
}

function SmallTag({
  label,
  tone = 'gray',
}: {
  label: string;
  tone?: 'gray' | 'blue' | 'gold' | 'green';
}) {
  let bg = 'rgba(255,255,255,0.08)';
  let color = '#E8E8E8';

  if (tone === 'blue') {
    bg = 'rgba(125,180,255,0.16)';
    color = '#BBD3FF';
  } else if (tone === 'gold') {
    bg = 'rgba(255,204,102,0.16)';
    color = '#FFD27C';
  } else if (tone === 'green') {
    bg = 'rgba(66,184,131,0.18)';
    color = '#A9FFCB';
  }

  return (
    <span
      style={{
        padding: '4px 8px',
        borderRadius: 999,
        fontSize: 11,
        fontWeight: 700,
        background: bg,
        color,
      }}
    >
      {label}
    </span>
  );
}

function InfoLine({
  label,
  value,
}: {
  label: string;
  value?: string | null;
}) {
  return (
    <div style={{ marginBottom: 8 }}>
      <span style={{ opacity: 0.65, marginRight: 8 }}>{label}:</span>
      <span>{value || '—'}</span>
    </div>
  );
}

function formatDate(value?: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

export default function WalletPage() {
  const [tickets, setTickets] = useState<WalletTicket[]>([]);
  const [summary, setSummary] = useState<WalletMe | null>(null);
  const [raw, setRaw] = useState<unknown>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [mintingId, setMintingId] = useState<string | null>(null);
  const [mintMessage, setMintMessage] = useState('');

  const { wallets } = useWallets();
  const connectedWallet = wallets?.[0]?.address || '';

  async function refreshAll() {
    const [walletSummary, ticketsData] = await Promise.all([
      getWalletMe(),
      getWalletTickets(),
    ]);

    setSummary((walletSummary || null) as WalletMe);
    setRaw(ticketsData);
    setTickets(normalizeTickets(ticketsData));
  }

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        setError('');
        await refreshAll();
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load wallet');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const activeCount = useMemo(
    () => tickets.filter((t) => (t.status || '').toLowerCase() === 'active').length,
    [tickets]
  );

  const usedCount = useMemo(
    () => tickets.filter((t) => (t.status || '').toLowerCase() === 'used').length,
    [tickets]
  );

  const expiredCount = useMemo(
    () => tickets.filter((t) => (t.status || '').toLowerCase() === 'expired').length,
    [tickets]
  );

  const refundedCount = useMemo(
    () => tickets.filter((t) => (t.status || '').toLowerCase() === 'refunded').length,
    [tickets]
  );

  async function handleMint(ticketId: string) {
    try {
      setMintingId(ticketId);
      setMintMessage('');
      setError('');
      await mintTicket(ticketId);
      setMintMessage(`NFT minted successfully for ticket ${ticketId.slice(0, 8)}.`);
      await refreshAll();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Mint failed');
    } finally {
      setMintingId(null);
    }
  }

  return (
    <div>
      <PageHeader
        title="My Wallet"
        subtitle="Platform ticket wallet with NFT-style ownership, mint state, and marketplace visibility."
      />

      {(connectedWallet || summary?.wallet_address) ? (
        <div className="card" style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 13, opacity: 0.7, marginBottom: 8 }}>Connected Wallet</div>
          <div style={{ fontWeight: 800, wordBreak: 'break-all' }}>
            {connectedWallet || summary?.wallet_address}
          </div>
        </div>
      ) : null}

      {loading ? <div className="card">Loading wallet...</div> : null}

      {error ? (
        <div className="card" style={{ border: '1px solid rgba(255,80,80,0.35)' }}>
          <div style={{ fontWeight: 700, marginBottom: 8 }}>Unable to load wallet</div>
          <div style={{ opacity: 0.8 }}>{error}</div>
        </div>
      ) : null}

      {mintMessage ? (
        <div className="card" style={{ border: '1px solid rgba(66,184,131,0.35)', marginBottom: 20 }}>
          <div style={{ color: '#A9FFCB', fontWeight: 700 }}>{mintMessage}</div>
        </div>
      ) : null}

      <div className="grid grid-4" style={{ marginBottom: 24 }}>
        <div className="card">
          <div style={{ fontSize: 13, opacity: 0.7, marginBottom: 8 }}>Total Tickets</div>
          <div style={{ fontSize: 30, fontWeight: 800 }}>
            {summary?.total_tickets ?? tickets.length}
          </div>
        </div>
        <div className="card">
          <div style={{ fontSize: 13, opacity: 0.7, marginBottom: 8 }}>Active</div>
          <div style={{ fontSize: 30, fontWeight: 800 }}>{activeCount}</div>
        </div>
        <div className="card">
          <div style={{ fontSize: 13, opacity: 0.7, marginBottom: 8 }}>Minted</div>
          <div style={{ fontSize: 30, fontWeight: 800 }}>
            {summary?.minted_tickets ??
              tickets.filter((t) => (t.mint_status || '').toLowerCase() === 'minted').length}
          </div>
        </div>
        <div className="card">
          <div style={{ fontSize: 13, opacity: 0.7, marginBottom: 8 }}>Listed</div>
          <div style={{ fontSize: 30, fontWeight: 800 }}>
            {summary?.listed_tickets ?? tickets.filter((t) => t.is_listed).length}
          </div>
        </div>
      </div>

      <div className="grid grid-3" style={{ marginBottom: 24 }}>
        <div className="card">
          <div style={{ fontSize: 13, opacity: 0.7, marginBottom: 8 }}>Used</div>
          <div style={{ fontSize: 30, fontWeight: 800 }}>{usedCount}</div>
        </div>
        <div className="card">
          <div style={{ fontSize: 13, opacity: 0.7, marginBottom: 8 }}>Expired</div>
          <div style={{ fontSize: 30, fontWeight: 800 }}>{expiredCount}</div>
        </div>
        <div className="card">
          <div style={{ fontSize: 13, opacity: 0.7, marginBottom: 8 }}>Refunded</div>
          <div style={{ fontSize: 30, fontWeight: 800 }}>{refundedCount}</div>
        </div>
      </div>

      {tickets.length === 0 ? (
        <div className="card">
          <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 10 }}>
            No tickets yet
          </div>
          <div style={{ opacity: 0.75, lineHeight: 1.6 }}>
            Your wallet does not currently contain any ticket records returned by the backend.
          </div>

          <details style={{ marginTop: 16 }}>
            <summary style={{ cursor: 'pointer', opacity: 0.8 }}>
              Show raw backend response
            </summary>
            <pre
              style={{
                marginTop: 12,
                whiteSpace: 'pre-wrap',
                fontSize: 12,
                opacity: 0.75,
              }}
            >
              {JSON.stringify(raw, null, 2)}
            </pre>
          </details>
        </div>
      ) : (
        <div className="grid grid-2">
          {tickets.map((ticket) => {
            const mintStatus = (ticket.mint_status || 'not_minted').toLowerCase();
            const canMint =
              (ticket.status || '').toLowerCase() === 'active' && mintStatus !== 'minted';

            return (
              <div className="card" key={ticket.id}>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: 12,
                    marginBottom: 16,
                  }}
                >
                  <div>
                    <div style={{ fontSize: 20, fontWeight: 700 }}>
                      {ticket.title || `Ticket #${ticket.id.slice(0, 8)}`}
                    </div>
                    <div className="muted small" style={{ marginTop: 6 }}>
                      {ticket.artist || 'Unknown artist'} {ticket.city ? `· ${ticket.city}` : ''}
                    </div>
                  </div>
                  <StatusBadge status={ticket.status} />
                </div>

                <InfoLine label="Event ID" value={ticket.event_id} />
                <InfoLine label="Event UUID" value={ticket.event_uuid} />
                <InfoLine label="Order ID" value={ticket.order_id} />
                <InfoLine label="Token ID" value={ticket.token_id || 'Not minted'} />
                <InfoLine label="Chain" value={ticket.chain || 'Off-chain mock'} />
                <InfoLine label="Owner Wallet" value={shortAddr(ticket.owner_wallet)} />
                <InfoLine label="Tx Hash" value={ticket.tx_hash || '—'} />
                <InfoLine label="Created At" value={formatDate(ticket.created_at)} />
                <InfoLine label="Minted At" value={formatDate(ticket.minted_at)} />

                <div style={{ marginTop: 12, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  <SmallTag
                    label={mintStatus === 'minted' ? 'Minted' : 'Not Minted'}
                    tone={mintStatus === 'minted' ? 'blue' : 'gray'}
                  />
                  {ticket.is_listed ? <SmallTag label="Listed" tone="gold" /> : null}
                </div>

                <div style={{ marginTop: 16, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                  <Link className="btn" href={`/wallet/${ticket.id}`}>
                    View Detail
                  </Link>

                  <button
                    className="btn ghost"
                    onClick={() => void handleMint(ticket.id)}
                    disabled={!canMint || mintingId === ticket.id}
                  >
                    {mintingId === ticket.id
                      ? 'Minting...'
                      : mintStatus === 'minted'
                        ? 'Already Minted'
                        : 'Mint NFT'}
                  </button>

                  {ticket.event_uuid &&
                  ['active', 'used'].includes((ticket.status || '').toLowerCase()) ? (
                    <Link className="btn ghost" href={`/chat/${ticket.event_uuid}`}>
                      Open Chat
                    </Link>
                  ) : null}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}