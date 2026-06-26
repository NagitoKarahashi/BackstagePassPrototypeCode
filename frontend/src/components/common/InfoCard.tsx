export function InfoCard({ title, value, hint }: { title: string; value: React.ReactNode; hint?: string }) {
  return (
    <div className="card">
      <div className="muted small">{title}</div>
      <div className="kpi">{value}</div>
      {hint ? <div className="muted small">{hint}</div> : null}
    </div>
  );
}
