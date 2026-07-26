export default function StatsCard({ icon, value, label }) {
  return (
    <div className="stats-card">
      <div className="stats-card-icon" aria-hidden="true">{icon}</div>
      <div className="stats-card-value">{value}</div>
      <div className="stats-card-label">{label}</div>
    </div>
  );
}
