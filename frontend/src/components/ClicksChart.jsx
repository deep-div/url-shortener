import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

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
      <div
        style={{
          fontFamily: 'var(--font-mono)',
          fontSize: '11px',
          color: 'var(--text-muted)',
          marginBottom: '4px',
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontFamily: 'var(--font-mono)',
          fontSize: '15px',
          fontWeight: 600,
          color: 'var(--accent-dark)',
        }}
      >
        {payload[0].value.toLocaleString()} clicks
      </div>
    </div>
  );
}

/**
 * Area chart for clicks over time.
 * @param {{ data: Array<{ date: string, clicks: number }> }} props
 */
export default function ClicksChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="chart-card">
        <div className="empty-state">
          <div className="empty-title">No click data yet</div>
          <div className="empty-desc">Share your link to start seeing clicks here.</div>
        </div>
      </div>
    );
  }

  const total = data.reduce((s, d) => s + d.clicks, 0);

  return (
    <div className="chart-card">
      <div className="chart-header">
        <div>
          <div className="chart-title">Clicks over time</div>
          <div className="chart-subtitle">{data.length}-day window</div>
        </div>
        <span className="badge badge-accent">{total.toLocaleString()} total</span>
      </div>

      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={data} margin={{ top: 4, right: 0, left: -24, bottom: 0 }}>
          <defs>
            <linearGradient id="clicksGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#8CB418" stopOpacity={0.25} />
              <stop offset="95%" stopColor="#8CB418" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="#E2DED7" strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="date"
            tick={{ fill: '#8A8A8A', fontSize: 11, fontFamily: 'JetBrains Mono, monospace' }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(val) => val.slice(5)}
          />
          <YAxis
            tick={{ fill: '#8A8A8A', fontSize: 11, fontFamily: 'JetBrains Mono, monospace' }}
            axisLine={false}
            tickLine={false}
            allowDecimals={false}
          />
          <Tooltip
            content={<CustomTooltip />}
            cursor={{ stroke: '#8CB418', strokeWidth: 1, strokeDasharray: '4 4' }}
          />
          <Area
            type="monotone"
            dataKey="clicks"
            stroke="#8CB418"
            strokeWidth={2}
            fill="url(#clicksGrad)"
            dot={false}
            activeDot={{ r: 4, fill: '#A8D520', stroke: 'white', strokeWidth: 2 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
