'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'next/navigation';
import { PageHeader } from '@/components/common/PageHeader';
import { getEventById } from '@/lib/api/events';
import { createOrder, payOrder, cancelOrder } from '@/lib/api/orders';
import type { EventItem } from '@/lib/types';

type OrderLike = {
  order_id?: string;
  id?: string;
  user_id?: string;
  event_id?: string;
  event_uuid?: string;
  qty?: number;
  total_amount?: number;
  status?: string;
};

function extractOrderObject(data: any): OrderLike | null {
  if (!data) return null;

  if (Array.isArray(data)) {
    const first = data[0];
    if (first && typeof first === 'object') return first as OrderLike;
    return null;
  }

  if (typeof data === 'object') {
    if (data.order && typeof data.order === 'object') return data.order as OrderLike;
    if (data.order_id || data.id) return data as OrderLike;
    if (data.data && typeof data.data === 'object') return data.data as OrderLike;
  }

  return null;
}

function extractOrderId(data: any): string | null {
  const obj = extractOrderObject(data);
  if (!obj) return null;
  return obj.order_id || obj.id || null;
}

function getRiskDecision(data: Record<string, unknown> | null): string {
  if (!data) return '';
  const risk =
    typeof data.risk === 'object' && data.risk
      ? (data.risk as Record<string, unknown>)
      : null;

  const value =
    data.decision ||
    data.status ||
    data.action ||
    risk?.decision ||
    risk?.status ||
    risk?.action;

  return typeof value === 'string' ? value.toLowerCase() : '';
}

function getRiskLevel(data: Record<string, unknown> | null): string {
  if (!data) return '';
  const risk =
    typeof data.risk === 'object' && data.risk
      ? (data.risk as Record<string, unknown>)
      : null;

  const value =
    data.risk_level ||
    data.level ||
    risk?.risk_level ||
    risk?.level ||
    risk?.label;

  return typeof value === 'string' ? value : '';
}

function getRiskMessage(data: Record<string, unknown> | null): string {
  if (!data) return '';
  const risk =
    typeof data.risk === 'object' && data.risk
      ? (data.risk as Record<string, unknown>)
      : null;

  const value =
    data.message ||
    data.detail ||
    data.reason ||
    risk?.message ||
    risk?.detail ||
    risk?.reason;

  return typeof value === 'string' ? value : '';
}

function InfoRow({
  label,
  value,
}: {
  label: string;
  value?: string | number | null;
}) {
  return (
    <div className="row" style={{ justifyContent: 'space-between', gap: 16 }}>
      <strong>{label}</strong>
      <span>{value ?? '—'}</span>
    </div>
  );
}

export default function EventDetailPage() {
  const params = useParams<{ eventId: string }>();

  const [event, setEvent] = useState<EventItem | null>(null);
  const [qty, setQty] = useState(1);

  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const [buying, setBuying] = useState(false);
  const [cancelling, setCancelling] = useState(false);

  const [latestOrder, setLatestOrder] = useState<OrderLike | null>(null);
  const [latestOrderResponse, setLatestOrderResponse] = useState<Record<string, unknown> | null>(null);
  const [latestPaidResult, setLatestPaidResult] = useState<any>(null);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        setMessage('');
        setError('');

        if (!params.eventId) return;
        const data = await getEventById(params.eventId);
        setEvent(data);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load event');
      } finally {
        setLoading(false);
      }
    })();
  }, [params.eventId]);

  const canCancel = useMemo(() => {
    return !!latestOrder && (latestOrder.status || '').toLowerCase() === 'created';
  }, [latestOrder]);

  async function handleCreateOnly() {
    try {
      setBuying(true);
      setError('');
      setMessage('');
      setLatestOrderResponse(null);

      if (!event) {
        throw new Error('Missing event data');
      }

      const created = await createOrder({
        event_id: event.id,
        quantity: Number(qty),
      });

      setLatestOrderResponse(created);

      const orderObj = extractOrderObject(created);
      const orderId = extractOrderId(created);

      if (!orderObj || !orderId) {
        throw new Error(`Order created but no order id returned: ${JSON.stringify(created)}`);
      }

      setLatestOrder({
        ...orderObj,
        order_id: orderId,
        status: orderObj.status || 'created',
      });

      const decision = getRiskDecision(created);
      if (decision.includes('blocked')) {
        setMessage(getRiskMessage(created) || 'Order blocked due to account risk.');
      } else if (decision.includes('review')) {
        setMessage(`Order #${orderId} created and flagged for review.`);
      } else {
        setMessage(`Order created successfully. Order #${orderId} is ready for payment.`);
      }

      setLatestPaidResult(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Create order failed');
    } finally {
      setBuying(false);
    }
  }

  async function handlePayLatestOrder() {
    try {
      setBuying(true);
      setError('');
      setMessage('');

      const orderId = latestOrder?.order_id || latestOrder?.id;
      if (!orderId) throw new Error('No created order available for payment');

      const paid = await payOrder(orderId);
      setLatestPaidResult(paid);
      setLatestOrder((prev) =>
        prev
          ? {
              ...prev,
              status: 'paid',
            }
          : prev
      );

      setMessage(`Purchase succeeded for order ${orderId}. Open wallet to verify tickets.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Pay order failed');
    } finally {
      setBuying(false);
    }
  }

  async function handleCreateAndPay() {
    try {
      setBuying(true);
      setError('');
      setMessage('');
      setLatestOrderResponse(null);

      if (!event) {
        throw new Error('Missing event data');
      }

      const created = await createOrder({
        event_id: event.id,
        quantity: Number(qty),
      });

      setLatestOrderResponse(created);

      const orderObj = extractOrderObject(created);
      const orderId = extractOrderId(created);

      if (!orderObj || !orderId) {
        throw new Error(`Order created but no order id returned: ${JSON.stringify(created)}`);
      }

      setLatestOrder({
        ...orderObj,
        order_id: orderId,
        status: orderObj.status || 'created',
      });

      const decision = getRiskDecision(created);
      if (decision.includes('blocked')) {
        setMessage(getRiskMessage(created) || 'Order blocked due to account risk.');
        return;
      }

      const paid = await payOrder(orderId);
      setLatestPaidResult(paid);
      setLatestOrder((prev) =>
        prev
          ? {
              ...prev,
              status: 'paid',
            }
          : prev
      );

      if (decision.includes('review')) {
        setMessage(`Order ${orderId} submitted and flagged for review.`);
      } else {
        setMessage(`Purchase succeeded for order ${orderId}. Open wallet to verify tickets.`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Purchase failed');
    } finally {
      setBuying(false);
    }
  }

  async function handleCancelLatestOrder() {
    try {
      setCancelling(true);
      setError('');
      setMessage('');

      const orderId = latestOrder?.order_id || latestOrder?.id;
      if (!orderId) throw new Error('No created order available to cancel');

      await cancelOrder(orderId);

      setLatestOrder((prev) =>
        prev
          ? {
              ...prev,
              status: 'cancelled',
            }
          : prev
      );

      setMessage(`Order ${orderId} has been cancelled and stock should be restored.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Cancel order failed');
    } finally {
      setCancelling(false);
    }
  }

  if (loading) return <div className="card">Loading event...</div>;
  if (error && !event) return <div className="card">{error}</div>;
  if (!event) return <div className="card">Event not found.</div>;

  const riskDecision = getRiskDecision(latestOrderResponse);
  const riskLevel = getRiskLevel(latestOrderResponse);
  const riskMessage = getRiskMessage(latestOrderResponse);

  const eventDescription =
  (event as any).desc ||
  (event as any).description ||
  'No event description provided.';

const eventPrice =
  (event as any).price ??
  (event as any).ticket_price ??
  '$45';

const eventStockLeft =
  (event as any).stock_left ??
  (event as any).remaining_stock ??
  (event as any).tickets_remaining ??
  0;

  return (
    <div>
      <PageHeader
        title={event.title || 'Event Detail'}
        subtitle="Review event details, create orders, and continue to payment."
      />

      <div className="grid grid-2">
        <div className="card">
          <div
            style={{
              width: '100%',
              aspectRatio: '3 / 4',
              borderRadius: 24,
              background: 'rgba(255,255,255,0.08)',
              display: 'grid',
              placeItems: 'center',
              overflow: 'hidden',
              marginBottom: 18,
            }}
          >
            {event.poster_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={event.poster_url}
                alt={event.title || 'event poster'}
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
              />
            ) : (
              <div style={{ fontSize: 28, fontWeight: 800, opacity: 0.35 }}>
                {event.title}
              </div>
            )}
          </div>

          <div className="small" style={{ opacity: 0.75, marginBottom: 12 }}>
            {[event.artist, event.city].filter(Boolean).join(' · ')}
          </div>

          <div style={{ fontSize: 18, lineHeight: 1.7, marginBottom: 18 }}>
            {eventDescription}
          </div>

          <InfoRow label="Genre" value={event.genre} />
          <InfoRow label="Start Time" value={event.start_time} />
          <InfoRow label="Event UUID" value={event.id} />
        </div>

        <div className="card">
          <div style={{ fontSize: 36, fontWeight: 900, marginBottom: 10 }}>
            Purchase panel
          </div>
          <div className="small" style={{ marginBottom: 18, opacity: 0.8 }}>
            Current frontend flow supports create, pay, cancel, and risk-aware order feedback.
          </div>

          <div style={{ marginBottom: 18 }}>
            <InfoRow label="Price" value={eventPrice} />
            <InfoRow label="Stock left" value={eventStockLeft} />
          </div>

          <input
            className="input"
            type="number"
            min={1}
            value={qty}
            onChange={(e) => setQty(Math.max(1, Number(e.target.value) || 1))}
            style={{ marginBottom: 18 }}
          />

          <div style={{ display: 'grid', gap: 12 }}>
            <button className="btn" onClick={handleCreateAndPay} disabled={buying}>
              {buying ? 'Processing...' : 'Create order and pay'}
            </button>

            <button className="btn secondary" onClick={handleCreateOnly} disabled={buying}>
              Create order only
            </button>

            <button className="btn ghost" onClick={handlePayLatestOrder} disabled={buying}>
              Pay latest order
            </button>

            <Link className="btn ghost" href={`/chat/${event.id}`}>
              Open Event Chat
            </Link>

            <Link className="btn ghost" href="/risk">
              Risk Overview
            </Link>

            <button
              className="btn ghost"
              onClick={handleCancelLatestOrder}
              disabled={!canCancel || cancelling}
            >
              {cancelling ? 'Cancelling...' : 'Cancel latest order'}
            </button>
          </div>

          {message ? (
            <div className="card" style={{ marginTop: 18 }}>
              <strong>Status</strong>
              <div style={{ marginTop: 10, whiteSpace: 'pre-wrap' }}>{message}</div>
            </div>
          ) : null}

          {error ? (
            <div
              className="card"
              style={{
                marginTop: 18,
                border: '1px solid rgba(255,80,80,0.35)',
                background: 'rgba(255,80,80,0.08)',
              }}
            >
              <strong>Error</strong>
              <div style={{ marginTop: 10, whiteSpace: 'pre-wrap' }}>{error}</div>
            </div>
          ) : null}

          {latestOrder ? (
            <div className="card" style={{ marginTop: 18 }}>
              <strong>Latest order</strong>
              <div style={{ marginTop: 10, display: 'grid', gap: 8 }}>
                <InfoRow label="Order ID" value={latestOrder.order_id || latestOrder.id} />
                <InfoRow label="Status" value={latestOrder.status} />
                <InfoRow label="Qty" value={latestOrder.qty} />
                <InfoRow label="Total" value={latestOrder.total_amount} />
              </div>
            </div>
          ) : null}

          {latestOrderResponse ? (
            <div className="card" style={{ marginTop: 18 }}>
              <strong>Risk feedback</strong>
              <div style={{ marginTop: 10, display: 'grid', gap: 8 }}>
                <InfoRow label="Decision" value={riskDecision || '—'} />
                <InfoRow label="Risk" value={riskLevel || '—'} />
                <InfoRow label="Message" value={riskMessage || '—'} />
              </div>
            </div>
          ) : null}

          {latestPaidResult ? (
            <details style={{ marginTop: 18 }}>
              <summary style={{ cursor: 'pointer' }}>Show payment result</summary>
              <pre style={{ whiteSpace: 'pre-wrap', marginTop: 12, opacity: 0.8 }}>
                {JSON.stringify(latestPaidResult, null, 2)}
              </pre>
            </details>
          ) : null}
        </div>
      </div>
    </div>
  );
}