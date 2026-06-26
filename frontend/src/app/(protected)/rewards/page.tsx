'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { PageHeader } from '@/components/common/PageHeader';
import { rewardsApi } from '@/lib/api/rewards';

type RewardSummary = {
  fan_points: number;
  badge_count: number;
  ledger_count: number;
};

function StatCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: string | number;
  hint?: string;
}) {
  return (
    <div className="card">
      <div style={{ fontSize: 14, opacity: 0.7, marginBottom: 8 }}>{label}</div>
      <div style={{ fontSize: 32, fontWeight: 700, lineHeight: 1.1 }}>{value}</div>
      {hint ? (
        <div style={{ fontSize: 13, opacity: 0.65, marginTop: 10 }}>{hint}</div>
      ) : null}
    </div>
  );
}

function ActionCard({
  title,
  description,
  href,
  buttonText,
}: {
  title: string;
  description: string;
  href: string;
  buttonText: string;
}) {
  return (
    <div className="card">
      <div style={{ fontSize: 20, fontWeight: 700, marginBottom: 10 }}>{title}</div>
      <div style={{ opacity: 0.75, lineHeight: 1.6, marginBottom: 18 }}>{description}</div>
      <Link className="btn" href={href}>
        {buttonText}
      </Link>
    </div>
  );
}

export default function RewardsPage() {
  const [summary, setSummary] = useState<RewardSummary | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const data = await rewardsApi.summary();
        setSummary(data as RewardSummary);
        setError('');
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load rewards summary');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div>
      <PageHeader
        title="Rewards"
        subtitle="Fan engagement summary for the current user. This page is currently powered by the stable summary API."
        actions={
          <div className="row">
            <Link className="btn secondary" href="/rewards/missions">
              Missions
            </Link>
            <Link className="btn ghost" href="/rewards/redeem">
              Redeem
            </Link>
          </div>
        }
      />

      {loading ? (
        <div className="card">Loading rewards summary...</div>
      ) : null}

      {error ? (
        <div className="card" style={{ border: '1px solid rgba(255,80,80,0.35)' }}>
          <div style={{ fontWeight: 700, marginBottom: 8 }}>Unable to load rewards</div>
          <div style={{ opacity: 0.8 }}>{error}</div>
        </div>
      ) : null}

      {summary ? (
        <>
          <div className="grid grid-3" style={{ marginBottom: 24 }}>
            <StatCard
              label="Fan Points"
              value={summary.fan_points}
              hint="Points accumulated through engagement and reward actions."
            />
            <StatCard
              label="Badges Earned"
              value={summary.badge_count}
              hint="Unlocked badge count from your participation history."
            />
            <StatCard
              label="Ledger Records"
              value={summary.ledger_count}
              hint="Number of point-related reward transactions recorded so far."
            />
          </div>

          <div className="grid grid-2">
            <ActionCard
              title="Mission Progress"
              description="View active missions, start available tasks, and claim completed rewards."
              href="/rewards/missions"
              buttonText="Open Missions"
            />
            <ActionCard
              title="Redeem Rewards"
              description="Browse redeemable items and exchange fan points for available rewards."
              href="/rewards/redeem"
              buttonText="Open Redeem"
            />
          </div>

          <div className="card" style={{ marginTop: 24 }}>
            <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 12 }}>Current integration status</div>
            <div style={{ opacity: 0.8, lineHeight: 1.7 }}>
              This version of the rewards page is intentionally connected to the stable
              <code style={{ marginLeft: 6, marginRight: 6 }}>/rewards/summary</code>
              endpoint first. Daily check-in and aggregated overview data can be added after the
              overview/check-in backend path is fully stabilized.
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}