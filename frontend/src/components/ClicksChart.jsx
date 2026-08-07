import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

function formatDay(val) {
  // "2026-08-05" -> "Aug 5"
  const d = new Date(`${val}T00:00:00`);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function formatYAxis(val) {
  if (val >= 1000) {
    const k = val / 1000;
    return `${Number.isInteger(k) ? k : k.toFixed(1)}K`;
  }
  return val;
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div
      style={{
        background: 'var(--surface)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-md)',
        padding: '10px 14px',
        boxShadow: 'var(--shadow-md)',
      }}
    >
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>
        {formatDay(label)}
      </div>
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 15, fontWeight: 600, color: 'var(--accent-dark)' }}>
        {payload[0].value.toLocaleString()} clicks
      </div>
    </div>
  );
}

/**
 * Clicks over time — smooth area/line chart.
 * @param {{ data: Array<{ date: string, clicks: number }> }} props
 */
export default function ClicksChart({ data }) {
  return (
    <div className="chart-card">
      <div className="chart-title">Clicks Over Time</div>

      {!data || data.length === 0 ? (
        <div className="empty-state">
          <div className="empty-title">No click data yet</div>
          <div className="empty-desc">Share your link to start seeing clicks here.</div>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={280}>
          <AreaChart data={data} margin={{ top: 12, right: 8, left: -18, bottom: 0 }}>
            <defs>
              <linearGradient id="clicksGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#6366F1" stopOpacity={0.22} />
                <stop offset="95%" stopColor="#6366F1" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="none" vertical={false} horizontal={false} />
            <XAxis
              dataKey="date"
              tick={{ fill: 'var(--text-faint)', fontSize: 12 }}
              axisLine={false}
              tickLine={false}
              tickFormatter={formatDay}
              padding={{ left: 12, right: 12 }}
            />
            <YAxis
              tick={{ fill: 'var(--text-faint)', fontSize: 12 }}
              axisLine={false}
              tickLine={false}
              allowDecimals={false}
              tickFormatter={formatYAxis}
              width={48}
            />
            <Tooltip
              content={<CustomTooltip />}
              cursor={{ stroke: '#6366F1', strokeWidth: 1, strokeDasharray: '4 4' }}
            />
            <Area
              type="monotone"
              dataKey="clicks"
              stroke="#6366F1"
              strokeWidth={2.5}
              fill="url(#clicksGrad)"
              dot={{ r: 4, fill: '#6366F1', stroke: '#fff', strokeWidth: 2 }}
              activeDot={{ r: 6, fill: '#4F46E5', stroke: '#fff', strokeWidth: 2 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
