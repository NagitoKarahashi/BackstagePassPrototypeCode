'use client';

import { useState } from 'react';
import { createListing } from '@/lib/api/marketplace';

type Props = {
  ticketId: string;
  open: boolean;
  onClose: () => void;
  onSuccess?: () => void;
};

export function ListForSaleModal({ ticketId, open, onClose, onSuccess }: Props) {
  const [price, setPrice] = useState('120');
  const [currency, setCurrency] = useState('USD');
  const [expiresAt, setExpiresAt] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  if (!open) return null;

  async function handleSubmit() {
    try {
      setSubmitting(true);
      setError('');
      setSuccess('');

      await createListing({
        ticket_id: ticketId,
        listing_price: Number(price),
        currency,
        expires_at: expiresAt || undefined,
      });

      setSuccess('Listing created successfully.');
      onSuccess?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Listing failed');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div style={overlayStyle}>
      <div className="card" style={modalStyle}>
        <div style={{ fontSize: 20, fontWeight: 800, marginBottom: 12 }}>List Ticket for Sale</div>

        <div style={{ marginBottom: 12 }}>
          <div className="muted small" style={{ marginBottom: 6 }}>Listing Price</div>
          <input
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            placeholder="120"
            style={inputStyle}
          />
        </div>

        <div style={{ marginBottom: 12 }}>
          <div className="muted small" style={{ marginBottom: 6 }}>Currency</div>
          <input
            value={currency}
            onChange={(e) => setCurrency(e.target.value)}
            placeholder="USD"
            style={inputStyle}
          />
        </div>

        <div style={{ marginBottom: 12 }}>
          <div className="muted small" style={{ marginBottom: 6 }}>Expires At (optional)</div>
          <input
            value={expiresAt}
            onChange={(e) => setExpiresAt(e.target.value)}
            placeholder="2026-05-01T12:00:00+00:00"
            style={inputStyle}
          />
        </div>

        {error ? <div style={{ color: '#ff9a9a', marginBottom: 12 }}>{error}</div> : null}
        {success ? <div style={{ color: '#7CFFB2', marginBottom: 12 }}>{success}</div> : null}

        <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
          <button className="btn ghost" onClick={onClose}>Close</button>
          <button className="btn" onClick={handleSubmit} disabled={submitting || !price.trim()}>
            {submitting ? 'Submitting...' : 'Create Listing'}
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
