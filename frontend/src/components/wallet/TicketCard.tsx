import Link from 'next/link';
import type { Ticket } from '@/lib/types';

function StatusBadge({ status }: { status?: string | null }) {
  const normalized = (status || 'unknown').toLowerCase();
  return (
    <span
      style={{
        padding: '4px 10px',
        borderRadius: 999,
        fontSize: 12,
        fontWeight: 700,
        background: 'rgba(255,255,255,0.08)',
        textTransform: 'uppercase',
      }}
    >
      {normalized}
    </span>
  );
}

function SmallTag({ label }: { label: string }) {
  return (
    <span
      style={{
        padding: '4px 8px',
        borderRadius: 999,
        fontSize: 11,
        fontWeight: 700,
        background: 'rgba(124, 255, 178, 0.12)',
        color: '#A9FFCB',
      }}
    >
      {label}
    </span>
  );
}

export function TicketCard({ ticket }: { ticket: Ticket }) {
  return (
    <Link href={`/wallet/${ticket.id}`} className="card" style={{ display: 'block' }}>
      <div className="row" style={{ justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <strong style={{ fontSize: 18 }}>NFT Ticket #{ticket.id.slice(0, 8)}</strong>
          <div className="muted small" style={{ marginTop: 6 }}>
            Event code: {ticket.event_id || 'Unknown'}
          </div>
        </div>
        <StatusBadge status={ticket.status} />
      </div>

      <div className="space" />

      <div className="muted small">Token ID: {ticket.token_id || 'Not issued'}</div>
      <div className="muted small">Chain: {ticket.chain || 'Off-chain mock'}</div>
      <div className="muted small">Order: {ticket.order_id || 'Unknown'}</div>
      <div className="muted small">Created: {ticket.created_at || 'Unknown'}</div>

      <div style={{ marginTop: 12, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {ticket.is_listed ? <SmallTag label="Listed" /> : null}
        {ticket.transfer_locked ? <SmallTag label="Transfer Locked" /> : null}
        {ticket.resale_allowed === false ? <SmallTag label="No Resale" /> : null}
      </div>
    </Link>
  );
}