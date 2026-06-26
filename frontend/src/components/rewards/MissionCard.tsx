export function MissionCard({
  mission,
  onStart,
  onClaim,
}: {
  mission: Record<string, unknown>;
  onStart: () => Promise<void>;
  onClaim: () => Promise<void>;
}) {
  const status = String(mission.status || 'not_started');
  return (
    <div className="card">
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <h3>{String(mission.title || 'Mission')}</h3>
        <span className="badge">{status}</span>
      </div>
      <div className="muted small">{String(mission.description || '')}</div>
      <div className="space" />
      <div className="small muted">Progress: {String(mission.progress || 0)} / {String(mission.target_value || 0)}</div>
      <div className="small muted">Reward: {String(mission.reward_points || 0)} pts</div>
      <div className="space" />
      <div className="row">
        {(status === 'not_started' || status === 'in_progress') && <button className="btn secondary" onClick={onStart}>Start</button>}
        {status === 'completed' && <button className="btn" onClick={onClaim}>Claim</button>}
      </div>
    </div>
  );
}
