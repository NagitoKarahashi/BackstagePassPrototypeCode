'use client';

import { useState } from 'react';
import { transferTicket } from '@/lib/api/tickets';

type Props = {
  ticketId: string;
  open: boolean;
  onClose: () => void;
  onSuccess?: () => void;
};

export function TransferTicketModal({ ticketId, open, onClose, onSuccess }: Props) {
  const [toUserId, setToUserId] = useState('');
  const [toWalletAddress, setToWalletAddress] = useState('');
  const [note, setNote] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  if (!open) return null;

  async function handleSubmit() {
    try {
      setSubmitting(true);
      setError('');
      setSuccess('');

      await transferTicket(ticketId, {
        to_user_id: toUserId,
        to_wallet_address: toWalletAddress || undefined,
        note: note || undefined,
        device_id: 'web-demo',
        ip_address: '127.0.0.1',
      });

      setSuccess('Ticket transferred successfully.');
      onSuccess?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Transfer failed');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div style={overlayStyle}>
      <div className="card" style={modalStyle}>
        <div style={{ fontSize: 20, fontWeight: 800, marginBottom: 12 }}>Transfer Ticket</div>

        <div style={{ marginBottom: 12 }}>
          <div className="muted small" style={{ marginBottom: 6 }}>Recipient User ID</div>
          <input
            value={toUserId}
            onChange={(e) => setToUserId(e.target.value)}
            placeholder="target profile id"
            style={inputStyle}
          />
        </div>

        <div style={{ marginBottom: 12 }}>
          <div className="muted small" style={{ marginBottom: 6 }}>Recipient Wallet Address</div>
          <input
            value={toWalletAddress}
            onChange={(e) => setToWalletAddress(e.target.value)}
            placeholder="0x..."
            style={inputStyle}
          />
        </div>

        <div style={{ marginBottom: 12 }}>
          <div className="muted small" style={{ marginBottom: 6 }}>Note</div>
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="gift to friend"
            style={{ ...inputStyle, minHeight: 90, resize: 'vertical' as const }}
          />
        </div>

        {error ? <div style={{ color: '#ff9a9a', marginBottom: 12 }}>{error}</div> : null}
        {success ? <div style={{ color: '#7CFFB2', marginBottom: 12 }}>{success}</div> : null}

        <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
          <button className="btn ghost" onClick={onClose}>Close</button>
          <button className="btn" onClick={handleSubmit} disabled={submitting || !toUserId.trim()}>
            {submitting ? 'Submitting...' : 'Confirm Transfer'}
          </button>
        </div>
      </div>
    </div>
  );
}

const overlayStyle: React.CSSProperties = {
  position: 'fixed',
  inset: 0,
  background: 'rgba(0,0,0,0.55)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  padding: 20,
  zIndex: 50,
};

const modalStyle: React.CSSProperties = {
  width: '100%',
  maxWidth: 560,
};

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '12px 14px',
  borderRadius: 12,
  border: '1px solid rgba(255,255,255,0.12)',
  background: 'rgba(255,255,255,0.04)',
  color: 'white',
};