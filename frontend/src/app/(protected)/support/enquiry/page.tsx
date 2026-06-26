'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { PageHeader } from '@/components/common/PageHeader';
import { createSupportEnquiry, getMySupportEnquiries } from '@/lib/api/support';

type EnquiryItem = {
  id?: string;
  category?: string;
  subject?: string;
  message?: string;
  status?: string;
  created_at?: string;
  source?: string;
};

function normalizeItems(data: any): EnquiryItem[] {
  if (Array.isArray(data)) return data;
  if (data && typeof data === 'object') {
    if (Array.isArray(data.items)) return data.items;
    if (Array.isArray(data.data)) return data.data;
  }
  return [];
}

export default function SupportEnquiryPage() {
  const searchParams = useSearchParams();

  const [category, setCategory] = useState('general');
  const [subject, setSubject] = useState('');
  const [message, setMessage] = useState('');
  const [orderId, setOrderId] = useState('');
  const [eventUuid, setEventUuid] = useState('');
  const [ticketId, setTicketId] = useState('');
  const [source, setSource] = useState<'manual' | 'chatbot' | 'refund_flow' | 'transfer_flow' | 'risk_flow'>('manual');

  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');
  const [items, setItems] = useState<EnquiryItem[]>([]);

  useEffect(() => {
    const qCategory = searchParams.get('category');
    const qSubject = searchParams.get('subject');
    const qOrderId = searchParams.get('order_id');
    const qEventUuid = searchParams.get('event_uuid');
    const qTicketId = searchParams.get('ticket_id');
    const qSource = searchParams.get('source');

    if (qCategory) setCategory(qCategory);
    if (qSubject) setSubject(qSubject);
    if (qOrderId) setOrderId(qOrderId);
    if (qEventUuid) setEventUuid(qEventUuid);
    if (qTicketId) setTicketId(qTicketId);
    if (
      qSource === 'manual' ||
      qSource === 'chatbot' ||
      qSource === 'refund_flow' ||
      qSource === 'transfer_flow' ||
      qSource === 'risk_flow'
    ) {
      setSource(qSource);
    }
  }, [searchParams]);

  useEffect(() => {
    (async () => {
      try {
        setHistoryLoading(true);
        const data = await getMySupportEnquiries(10, 0);
        setItems(normalizeItems(data));
      } catch {
        setItems([]);
      } finally {
        setHistoryLoading(false);
      }
    })();
  }, []);

  async function handleSubmit() {
    if (!subject.trim() || !message.trim()) return;

    try {
      setLoading(true);
      setError('');
      setSuccess('');

      await createSupportEnquiry({
        category: category as any,
        subject: subject.trim(),
        message: message.trim(),
        order_id: orderId || null,
        event_uuid: eventUuid || null,
        ticket_id: ticketId || null,
        source,
      });

      setSuccess('Your enquiry has been submitted successfully.');
      setMessage('');

      const data = await getMySupportEnquiries(10, 0);
      setItems(normalizeItems(data));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to submit enquiry');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="stack">
      <PageHeader
        title="Support Enquiry"
        subtitle="Contact human support for refund, transfer, risk, or ticket issues."
      />

      <div className="card" style={{ maxWidth: 760 }}>
        <div className="grid" style={{ gap: 14 }}>
          <div>
            <label className="small muted">Category</label>
            <select className="input" value={category} onChange={(e) => setCategory(e.target.value)}>
              <option value="general">General</option>
              <option value="refund">Refund</option>
              <option value="transfer">Transfer</option>
              <option value="ticket">Ticket</option>
              <option value="event">Event</option>
              <option value="risk">Risk</option>
              <option value="account">Account</option>
              <option value="technical">Technical</option>
            </select>
          </div>

          <div>
            <label className="small muted">Subject</label>
            <input
              className="input"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="Briefly describe your issue"
            />
          </div>

          <div>
            <label className="small muted">Message</label>
            <textarea
              className="textarea"
              rows={6}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Please provide more details so our support team can help you."
            />
          </div>

          <div className="grid" style={{ gridTemplateColumns: '1fr 1fr', gap: 14 }}>
            <div>
              <label className="small muted">Order ID (optional)</label>
              <input className="input" value={orderId} onChange={(e) => setOrderId(e.target.value)} />
            </div>
            <div>
              <label className="small muted">Ticket ID (optional)</label>
              <input className="input" value={ticketId} onChange={(e) => setTicketId(e.target.value)} />
            </div>
          </div>

          <div>
            <label className="small muted">Event UUID (optional)</label>
            <input className="input" value={eventUuid} onChange={(e) => setEventUuid(e.target.value)} />
          </div>

          {success ? (
            <div className="card" style={{ border: '1px solid rgba(66,184,131,0.35)', background: 'rgba(66,184,131,0.08)' }}>
              {success}
            </div>
          ) : null}

          {error ? (
            <div className="card" style={{ border: '1px solid rgba(255,80,80,0.35)', background: 'rgba(255,80,80,0.08)' }}>
              {error}
            </div>
          ) : null}

          <div>
            <button className="btn" onClick={handleSubmit} disabled={loading || !subject.trim() || !message.trim()}>
              {loading ? 'Submitting...' : 'Submit Enquiry'}
            </button>
          </div>
        </div>
      </div>

      <div className="card" style={{ maxWidth: 760 }}>
        <div style={{ fontWeight: 700, marginBottom: 12 }}>My recent enquiries</div>
        {historyLoading ? (
          <div className="small muted">Loading enquiries...</div>
        ) : items.length === 0 ? (
          <div className="small muted">No enquiries yet.</div>
        ) : (
          <div className="stack">
            {items.map((item, index) => (
              <div key={item.id || `item-${index}`} className="card" style={{ background: 'rgba(255,255,255,0.03)' }}>
                <div style={{ fontWeight: 700 }}>{item.subject || 'Untitled enquiry'}</div>
                <div className="small muted" style={{ marginTop: 6 }}>
                  Category: {item.category || 'general'} · Status: {item.status || 'open'} · Source: {item.source || 'manual'}
                </div>
                <div style={{ marginTop: 8, whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
                  {item.message || '—'}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}