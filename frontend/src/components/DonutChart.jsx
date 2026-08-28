import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { formatCompactNumber } from '../utils/format.js';

const COLORS = ['#6366F1', '#818CF8', '#A5B4FC', '#4F46E5', '#C7D2FE', '#4338CA'];

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const { name, value } = payload[0].payload;
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
        {value.toLocaleString()} clicks
      </div>
    </div>
  );
}

/**
 * Donut chart with legend. Renders raw counts pulled from the API.
 * @param {{ title: string, data: Record<string, number> }} props
 */
export default function DonutChart({ title, data }) {
  const entries = data ? Object.entries(data).sort((a, b) => b[1] - a[1]) : [];
  const chartData = entries.map(([name, value]) => ({ name, value }));

  return (
    <div className="metric-card">
      <div className="metric-card-head">
        <div className="metric-card-title">{title}</div>
      </div>

      {chartData.length === 0 ? (
        <div className="metric-empty">No data yet</div>
      ) : (
        <div className="donut-body">
          <div className="donut-viz">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={46}
                  outerRadius={70}
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
          <div className="donut-legend2">
            {chartData.map((item, i) => (
              <div key={item.name} className="donut-leg-row">
                <span className="donut-leg-dot" style={{ background: COLORS[i % COLORS.length] }} />
                <span className="donut-leg-name" title={item.name || 'Unknown'}>{item.name || 'Unknown'}</span>
                <span className="donut-leg-val" title={item.value.toLocaleString()}>{formatCompactNumber(item.value)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
