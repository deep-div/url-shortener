/**
 * A single stat metric card.
 * @param {{ icon: React.ReactNode, value: string|number, label: string }} props
 */
export default function StatsCard({ icon, value, label }) {
  return (
    <div className="stats-card">
      {icon && (
        <div className="stats-card-icon" aria-hidden="true">
          {icon}
        </div>
      )}
      <div className="stats-card-value">{value ?? '—'}</div>
      <div className="stats-card-label">{label}</div>
    </div>
  );
}
