import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

const COLORS = ['#A8D520', '#8CB418', '#6B9A0E', '#3D5200', '#C4E86B', '#9E9E9E'];

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const { name, value, percent } = payload[0].payload;
  return (
    <div style={{
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius-md)',
      padding: '8px 12px',
      boxShadow: 'var(--shadow-md)',
    }}>
      <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text)' }}>{name}</div>
      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
        {value.toLocaleString()} ({(percent * 100).toFixed(0)}%)
      </div>
    </div>
  );
}

export default function DonutChart({ title, data }) {
  if (!data || Object.keys(data).length === 0) return null;

  const total = Object.values(data).reduce((s, v) => s + v, 0);
  const sorted = Object.entries(data).sort((a, b) => b[1] - a[1]);

  // Top 5 for the donut, rest merged into "Others"
  const top5 = sorted.slice(0, 5);
  const othersSum = sorted.slice(5).reduce((s, [, v]) => s + v, 0);
  const chartData = top5.map(([name, value]) => ({ name, value, percent: value / total }));
  if (othersSum > 0) {
    chartData.push({ name: 'Others', value: othersSum, percent: othersSum / total });
  }

  // Full sorted list for the scrollable table
  const allEntries = sorted.map(([name, value]) => ({ name, value }));

  return (
    <div className="donut-card">
      <div className="donut-title">{title}</div>
      <div className="donut-content">
        <div className="donut-chart-wrap">
          <ResponsiveContainer width="100%" height={160}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={42}
                outerRadius={68}
                paddingAngle={2}
                dataKey="value"
                stroke="none"
              >
                {chartData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="donut-legend">
          {chartData.map((item, i) => (
            <div key={item.name} className="donut-legend-item">
              <span className="donut-legend-dot" style={{ background: COLORS[i % COLORS.length] }} />
              <span className="donut-legend-name">{item.name}</span>
              <span className="donut-legend-value">{(item.percent * 100).toFixed(0)}%</span>
            </div>
          ))}
        </div>
      </div>

      {/* Full scrollable list */}
      <div className="donut-list-wrap">
        <div className="donut-list-header">
          <span>{title}</span>
          <span>Clicks</span>
        </div>
        <div className="donut-list">
          {allEntries.map((item) => (
            <div key={item.name} className="donut-list-row">
              <span className="donut-list-name">{item.name || 'Unknown'}</span>
              <span className="donut-list-count">{item.value.toLocaleString()}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
