'use client';

import { useEffect, useState } from 'react';
import { PageHeader } from '@/components/common/PageHeader';
import { getMyRiskOverview } from '@/lib/api/risk';

export default function RiskOverviewPage() {
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    getMyRiskOverview().then(setData).catch((e) => setError(e.message));
  }, []);

  const level = String(data?.risk_level ?? data?.level ?? '-');
  const score = String(data?.risk_score ?? data?.score ?? '-');
  const summary = String(
    data?.user_message ??
    data?.message ??
    data?.detail ??
    data?.recommended_action ??
    'No summary returned.'
  );

  return (
    <div>
      <PageHeader
        title="Risk Overview"
        subtitle="Current-user account risk status from /risk/me"
      />

      {error ? (
        <div className="card" style={{ border: '1px solid rgba(255,80,80,0.35)' }}>
          <div style={{ fontWeight: 700, marginBottom: 8 }}>Unable to load risk overview</div>
          <div style={{ opacity: 0.8 }}>{error}</div>
        </div>
      ) : null}

      <div className="grid grid-3">
        <div className="card">
          <div className="muted small">Risk level</div>
          <div style={{ fontSize: 32, fontWeight: 800, marginTop: 8 }}>{level}</div>
        </div>
        <div className="card">
          <div className="muted small">Risk score</div>
          <div style={{ fontSize: 32, fontWeight: 800, marginTop: 8 }}>{score}</div>
        </div>
        <div className="card">
          <div className="muted small">Summary</div>
          <div style={{ marginTop: 8, lineHeight: 1.6 }}>{summary}</div>
        </div>
      </div>

      <div className="space" />

      <div className="grid grid-2">
        <div className="card">
          <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 10 }}>Overview payload</div>
          <pre className="small muted" style={{ whiteSpace: 'pre-wrap' }}>
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>

        <div className="card">
          <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 10 }}>Signals</div>
          <pre className="small muted" style={{ whiteSpace: 'pre-wrap' }}>
            {JSON.stringify(data?.signals ?? {}, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
}