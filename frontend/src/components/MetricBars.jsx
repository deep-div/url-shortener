import { useState } from 'react';
import { formatCompactNumber } from '../utils/format.js';

/**
 * Ranked horizontal-bar list. Renders raw counts pulled from the API — no
 * aggregation in the UI; bar width is purely a relative fill vs. the top value.
 *
 * Two modes:
 *   - single:  <MetricBars title="Top Browsers" data={by_browser} />
 *   - toggled: <MetricBars tabs={[{ label:'Countries', data }, { label:'Cities', data }]} scroll />
 *
 * @param {{
 *   title?: string,
 *   data?: Record<string, number>,
 *   tabs?: Array<{ label: string, data: Record<string, number> }>,
 *   scroll?: boolean,
 * }} props
 */
export default function MetricBars({ title, data, tabs, scroll = false }) {
  const [active, setActive] = useState(0);
  const activeData = tabs ? tabs[active].data : data;
  const heading = tabs ? `Top ${tabs[active].label}` : title;

  const entries = activeData
    ? Object.entries(activeData).sort((a, b) => b[1] - a[1])
    : [];
  const max = entries.length ? entries[0][1] : 0;

  return (
    <div className="metric-card">
      <div className="metric-card-head">
        <div className="metric-card-title">{heading}</div>
        {tabs && (
          <div className="metric-toggle" role="tablist">
            {tabs.map((t, i) => (
              <button
                key={t.label}
                role="tab"
                aria-selected={i === active}
                className={`metric-toggle-btn${i === active ? ' active' : ''}`}
                onClick={() => setActive(i)}
              >
                {t.label}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className={`metric-list${scroll ? ' metric-list-scroll' : ''}`}>
        {entries.length === 0 ? (
          <div className="metric-empty">No data yet</div>
        ) : (
          entries.map(([name, value]) => (
            <div key={name} className="metric-row">
              <span className="metric-name" title={name || 'Unknown'}>{name || 'Unknown'}</span>
              <span className="metric-track">
                <span
                  className="metric-fill"
                  style={{ width: max ? `${(value / max) * 100}%` : '0%' }}
                />
              </span>
              <span className="metric-value" title={value.toLocaleString()}>{formatCompactNumber(value)}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
