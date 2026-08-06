import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius-md)',
      padding: '8px 12px',
      boxShadow: 'var(--shadow-md)',
    }}>
      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 2 }}>
        {label}:00
      </div>
      <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--accent-dark)' }}>
        {payload[0].value.toLocaleString()} clicks
      </div>
    </div>
  );
}

/**
 * Bar chart showing clicks distribution across hours of the day.
 * @param {{ data: Record<string, number> }} props - peak_hours from API
 */
export default function PeakHoursChart({ data }) {
  if (!data || Object.keys(data).length === 0) return null;

  // Build full 24h array so chart always shows complete day
  const chartData = Array.from({ length: 24 }, (_, i) => ({
    hour: String(i).padStart(2, '0'),
    clicks: data[String(i)] || 0,
  }));

  return (
    <div className="chart-card">
      <div className="chart-header">
        <div>
          <div className="chart-title">Peak Hours</div>
          <div className="chart-subtitle">Clicks by hour of day</div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={chartData} margin={{ top: 4, right: 0, left: -24, bottom: 0 }}>
          <CartesianGrid stroke="#E2DED7" strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="hour"
            tick={{ fill: '#8A8A8A', fontSize: 10, fontFamily: 'JetBrains Mono, monospace' }}
            axisLine={false}
            tickLine={false}
            interval={2}
          />
          <YAxis
            tick={{ fill: '#8A8A8A', fontSize: 10, fontFamily: 'JetBrains Mono, monospace' }}
            axisLine={false}
            tickLine={false}
            allowDecimals={false}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(168, 213, 32, 0.08)' }} />
          <Bar
            dataKey="clicks"
            fill="#A8D520"
            radius={[4, 4, 0, 0]}
            maxBarSize={24}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
