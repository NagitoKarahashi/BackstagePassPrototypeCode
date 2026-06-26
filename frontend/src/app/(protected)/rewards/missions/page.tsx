'use client';

import { useEffect, useState } from 'react';
import { PageHeader } from '@/components/common/PageHeader';
import { rewardsApi } from '@/lib/api/rewards';
import { MissionCard } from '@/components/rewards/MissionCard';

export default function MissionsPage() {
  const [items, setItems] = useState<Record<string, unknown>[]>([]);
  const [message, setMessage] = useState('Mission progress may update after order, chat, and check-in actions.');

  async function refresh() {
    const data = await rewardsApi.missions();
    setItems(data.items);
  }

  useEffect(() => { refresh().catch((e) => setMessage(e.message)); }, []);

  return (
    <div>
      <PageHeader title="Missions" subtitle="Real API page with minimal mission system." />
      <div className="grid grid-2">
        {items.map((mission) => (
          <MissionCard
            key={String(mission.mission_id)}
            mission={mission}
            onStart={async () => { await rewardsApi.startMission(String(mission.mission_id)); await refresh(); }}
            onClaim={async () => { await rewardsApi.claimMission(String(mission.mission_id)); await refresh(); }}
          />
        ))}
      </div>
      <div className="space" />
      <div className="muted small">{message}</div>
    </div>
  );
}
