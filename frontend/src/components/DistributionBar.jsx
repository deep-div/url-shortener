/**
 * Horizontal bar breakdown for a single dimension (device, browser, OS, etc.)
 * @param {{ title: string, data: Record<string, number> }} props
 */
export default function DistributionBar({ title, data }) {
  if (!data || Object.keys(data).length === 0) return null;

  const entries = Object.entries(data)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6);

  const max = entries[0]?.[1] || 1;

  return (
    <div className="distribution-card">
      <div className="distribution-title">{title}</div>
      {entries.map(([name, count]) => (
        <div key={name} className="dist-item">
          <div className="dist-item-header">
            <span className="dist-item-name">{name || 'Unknown'}</span>
            <span className="dist-item-count">{count.toLocaleString()}</span>
          </div>
          <div
            className="dist-track"
            role="progressbar"
            aria-valuenow={count}
            aria-valuemax={max}
            aria-label={`${name}: ${count}`}
          >
            <div
              className="dist-fill"
              style={{ width: `${(count / max) * 100}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
