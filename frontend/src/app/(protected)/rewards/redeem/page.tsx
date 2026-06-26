'use client';

import { useEffect, useState } from 'react';
import { PageHeader } from '@/components/common/PageHeader';
import { rewardsApi } from '@/lib/api/rewards';

export default function RedeemPage() {
  const [catalog, setCatalog] = useState<Record<string, unknown>[]>([]);
  const [redemptions, setRedemptions] = useState<Record<string, unknown>[]>([]);
  const [message, setMessage] = useState('');

  async function refresh() {
    const [catalogData, redemptionData] = await Promise.all([rewardsApi.catalog(), rewardsApi.myRedemptions()]);
    setCatalog(catalogData.items);
    setRedemptions(redemptionData.items);
  }

  useEffect(() => { refresh().catch((e) => setMessage(e.message)); }, []);

  return (
    <div>
      <PageHeader title="Redeem Rewards" subtitle="Real catalog + redemption history. Good optional Phase 1 enhancement." />
      <div className="grid grid-2">
        <div className="card">
          <h3>Catalog</h3>
          {catalog.map((item) => (
            <div key={String(item.id)} style={{ padding: '12px 0', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
              <div><strong>{String(item.title || '')}</strong></div>
              <div className="small muted">Cost: {String(item.cost_points || 0)} pts</div>
              <div className="space" />
              <button className="btn secondary" onClick={async () => { await rewardsApi.redeem(String(item.id)); await refresh(); }}>Redeem</button>
            </div>
          ))}
        </div>
        <div className="card">
          <h3>My redemptions</h3>
          <pre className="small muted" style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(redemptions, null, 2)}</pre>
        </div>
      </div>
      <div className="space" />
      <div className="muted small">{message}</div>
    </div>
  );
}
