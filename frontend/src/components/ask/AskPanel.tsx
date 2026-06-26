'use client';

import Link from 'next/link';
import { useMemo, useState } from 'react';
import { usePathname } from 'next/navigation';
import { getPrivyAccessToken } from '@/lib/auth/privy-token';

function resolveAskUrl() {
  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || '';
  if (!apiBase) return '/api/v1/ask';
  return `${apiBase.replace(/\/$/, '')}/ask`;
}

function stringifyValue(value: unknown): string {
  if (typeof value === 'string') return value;
  if (value == null) return '';
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function extractDisplayAnswer(response: Record<string, unknown> | null): string {
  if (!response) return '';

  const directCandidates = [
    response.answer,
    response.reply,
    response.response,
    response.text,
    response.message,
  ];

  for (const item of directCandidates) {
    if (typeof item === 'string' && item.trim()) return item;
  }

  if (response.data && typeof response.data === 'object') {
    const data = response.data as Record<string, unknown>;
    const nestedCandidates = [
      data.answer,
      data.reply,
      data.response,
      data.text,
      data.message,
    ];
    for (const item of nestedCandidates) {
      if (typeof item === 'string' && item.trim()) return item;
    }
  }

  return '';
}

export default function AskPanel() {
  const pathname = usePathname();
  const [question, setQuestion] = useState('');
  const [response, setResponse] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);
  const [requestError, setRequestError] = useState('');
  const [collapsed, setCollapsed] = useState(
    pathname.startsWith('/chat') || pathname.startsWith('/risk')
  );

  const askUrl = useMemo(() => resolveAskUrl(), []);

  async function handleAsk() {
    if (!question.trim()) return;

    try {
      setLoading(true);
      setRequestError('');
      setResponse(null);

      const token = await getPrivyAccessToken();

      const res = await fetch(askUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ question }),
        cache: 'no-store',
      });

      let data: Record<string, unknown> = {};
      try {
        data = await res.json();
      } catch {
        data = {};
      }

      if (!res.ok) {
        throw new Error(
          stringifyValue(data?.detail) ||
            stringifyValue(data?.message) ||
            `Ask failed: ${res.status}`
        );
      }

      setResponse(data);
    } catch (e) {
      setRequestError(e instanceof Error ? e.message : 'Ask request failed');
    } finally {
      setLoading(false);
    }
  }

  const answer = extractDisplayAnswer(response);
  const blocked = response?.blocked === true || response?.restricted === true;
  const riskLevel =
    typeof response?.risk_level === 'string'
      ? response.risk_level
      : typeof response?.level === 'string'
      ? response.level
      : typeof response?.risk === 'object' && response?.risk
      ? String((response.risk as Record<string, unknown>).level || '')
      : '';

  const citations = Array.isArray(response?.citations)
    ? response.citations
    : response?.data &&
      typeof response.data === 'object' &&
      Array.isArray((response.data as Record<string, unknown>).citations)
    ? ((response.data as Record<string, unknown>).citations as unknown[])
    : [];

  const intent =
    typeof response?.intent === 'string'
      ? response.intent
      : response?.data &&
        typeof response.data === 'object' &&
        typeof (response.data as Record<string, unknown>).intent === 'string'
      ? String((response.data as Record<string, unknown>).intent)
      : '';

  const enquiryHref = useMemo(() => {
    const params = new URLSearchParams();

    if (intent === 'refund' || intent === 'transfer') {
      params.set('category', intent);
    } else if (riskLevel) {
      params.set('category', 'risk');
    } else {
      params.set('category', 'general');
    }

    params.set('source', 'chatbot');

    if (question.trim()) {
      params.set('subject', question.trim().slice(0, 120));
    }

    return `/support/enquiry?${params.toString()}`;
  }, [intent, riskLevel, question]);

  return (
    <div
      className="card"
      style={{
        position: 'fixed',
        right: 16,
        bottom: 16,
        width: collapsed ? 220 : 360,
        zIndex: 40,
        padding: 16,
        display: 'flex',
        flexDirection: 'column',
        maxHeight: collapsed ? undefined : 'min(78vh, 720px)',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: 12,
          marginBottom: collapsed ? 0 : 10,
          flexShrink: 0,
        }}
      >
        <div style={{ fontSize: 18, fontWeight: 800 }}>Ask Assistant</div>
        <button
          type="button"
          className="btn ghost"
          onClick={() => setCollapsed((v) => !v)}
          style={{ padding: '6px 10px', minWidth: 'unset' }}
        >
          {collapsed ? 'Open' : 'Hide'}
        </button>
      </div>

      {!collapsed ? (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            minHeight: 0,
            gap: 10,
          }}
        >
          <textarea
            className="textarea"
            rows={3}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask about refund, transfer, risk, policy..."
            style={{ resize: 'none', minHeight: 88, maxHeight: 140, flexShrink: 0 }}
          />

          <button
            className="btn"
            onClick={handleAsk}
            disabled={loading || !question.trim()}
            style={{ flexShrink: 0 }}
          >
            {loading ? 'Thinking...' : 'Ask'}
          </button>

          <div
            style={{
              minHeight: 0,
              flex: 1,
              overflowY: 'auto',
              paddingRight: 4,
            }}
          >
            {requestError ? (
              <div
                className="card"
                style={{
                  border: '1px solid rgba(255,80,80,0.35)',
                  background: 'rgba(255,80,80,0.08)',
                  marginBottom: 10,
                }}
              >
                <div style={{ fontWeight: 700, marginBottom: 8 }}>Ask error</div>
                <div
                  className="small"
                  style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}
                >
                  {requestError}
                </div>
              </div>
            ) : null}

            {response ? (
              <>
                {blocked ? (
                  <div
                    className="card"
                    style={{
                      border: '1px solid rgba(255,80,80,0.35)',
                      background: 'rgba(255,80,80,0.08)',
                      marginBottom: 10,
                    }}
                  >
                    <div style={{ fontWeight: 700, marginBottom: 8 }}>Restricted response</div>
                    <div
                      className="small"
                      style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}
                    >
                      {stringifyValue(response?.message || response?.detail || response)}
                    </div>
                  </div>
                ) : null}

                {answer ? (
                  <div className="card" style={{ marginBottom: 10 }}>
                    <div style={{ fontWeight: 700, marginBottom: 8 }}>Answer</div>
                    <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>{answer}</div>
                  </div>
                ) : null}

                {(riskLevel || intent) && (
                  <div className="card" style={{ marginBottom: 10 }}>
                    <div style={{ fontWeight: 700, marginBottom: 8 }}>Assistant metadata</div>
                    <div className="small" style={{ lineHeight: 1.7 }}>
                      {intent ? <div>Intent: {intent}</div> : null}
                      {riskLevel ? <div>Risk: {riskLevel}</div> : null}
                    </div>
                  </div>
                )}

                {citations.length > 0 ? (
                  <div className="card" style={{ marginBottom: 10 }}>
                    <div style={{ fontWeight: 700, marginBottom: 8 }}>References</div>
                    <ul style={{ paddingLeft: 18, margin: 0 }}>
                      {citations.map((item, idx) => (
                        <li key={`${String(item)}-${idx}`} className="small">
                          {String(item)}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}

                <div className="card">
                  <div style={{ fontWeight: 700, marginBottom: 8 }}>Still need help?</div>
                  <div className="small" style={{ marginBottom: 10, lineHeight: 1.6 }}>
                    If the assistant did not fully solve your issue, submit a support enquiry.
                  </div>
                  <Link href={enquiryHref} className="btn secondary">
                    Open Support Enquiry
                  </Link>
                </div>
              </>
            ) : null}
          </div>
        </div>
      ) : null}
    </div>
  );
}