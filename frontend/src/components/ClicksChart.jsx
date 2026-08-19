import { useState, useRef, useEffect } from 'react';
import {
  AreaChart, Area,
  BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
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
      <div style={{ fontFamily: 'var(--font-display)', fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>
        {formatDay(label)}
      </div>
      <div style={{ fontFamily: 'var(--font-display)', fontSize: 15, fontWeight: 600, color: 'var(--accent-dark)' }}>
        {payload[0].value.toLocaleString()} clicks
      </div>
    </div>
  );
}

const RANGES = [
  { label: 'Today',        value: 'today' },
  { label: 'Yesterday',    value: 'yesterday' },
  { label: 'Last 7 days',  value: '7d' },
  { label: 'Last 14 days', value: '14d' },
  { label: 'Last 30 days', value: '30d' },
  { label: 'Last 90 days', value: '90d' },
  { label: 'All time',     value: 'all' },
];

function AreaIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <polyline points="3 17 9 9 14 13 21 4" />
      <polyline points="15 4 21 4 21 10" />
    </svg>
  );
}

function BarIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <rect x="3" y="12" width="4" height="9" rx="1" />
      <rect x="10" y="7" width="4" height="14" rx="1" />
      <rect x="17" y="3" width="4" height="18" rx="1" />
    </svg>
  );
}

function ChartTypeToggle({ chartType, onChartTypeChange }) {
  return (
    <div className="chart-type-toggle">
      <button
        className={`chart-type-btn${chartType === 'area' ? ' active' : ''}`}
        onClick={() => onChartTypeChange('area')}
        title="Line chart"
      >
        <AreaIcon />
      </button>
      <button
        className={`chart-type-btn${chartType === 'bar' ? ' active' : ''}`}
        onClick={() => onChartTypeChange('bar')}
        title="Bar chart"
      >
        <BarIcon />
      </button>
    </div>
  );
}

function ChevronIcon({ open }) {
  return (
    <svg
      width="14" height="14" viewBox="0 0 24 24"
      fill="none" stroke="currentColor" strokeWidth="2.5"
      strokeLinecap="round" strokeLinejoin="round"
      style={{ transition: 'transform 0.2s', transform: open ? 'rotate(180deg)' : 'rotate(0deg)' }}
    >
      <polyline points="6 9 12 15 18 9" />
    </svg>
  );
}

function RangeDropdown({ range, onRangeChange }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  const selected = RANGES.find((r) => r.value === range) ?? RANGES[RANGES.length - 1];

  useEffect(() => {
    function handleClick(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  return (
    <div className="range-dropdown" ref={ref}>
      <button className="range-dropdown-btn" onClick={() => setOpen((o) => !o)}>
        {selected.label}
        <ChevronIcon open={open} />
      </button>
      {open && (
        <div className="range-dropdown-menu">
          {RANGES.map((r) => (
            <button
              key={r.value}
              className={`range-dropdown-item${r.value === range ? ' active' : ''}`}
              onClick={() => { onRangeChange?.(r.value); setOpen(false); }}
            >
              {r.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function formatHour(val) {
  const h = Number(val);
  if (h === 0) return '12am';
  if (h < 12) return `${h}am`;
  if (h === 12) return '12pm';
  return `${h - 12}pm`;
}

function CustomHourTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', padding: '10px 14px', boxShadow: 'var(--shadow-md)' }}>
      <div style={{ fontFamily: 'var(--font-display)', fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>
        {formatHour(label)}
      </div>
      <div style={{ fontFamily: 'var(--font-display)', fontSize: 15, fontWeight: 600, color: 'var(--accent-dark)' }}>
        {payload[0].value.toLocaleString()} clicks
      </div>
    </div>
  );
}

export default function ClicksChart({ data, peakHours, range = 'all', onRangeChange }) {
  const [chartType, setChartType] = useState('area');
  const [viewTab, setViewTab] = useState('days');

  const hoursData = peakHours
    ? Array.from({ length: 24 }, (_, i) => ({ hour: String(i), clicks: peakHours[String(i)] ?? 0 }))
    : [];

  const isHours = viewTab === 'hours';
  const activeData = isHours ? hoursData : data;
  const isEmpty = !activeData || activeData.length === 0 || (isHours && activeData.every(d => d.clicks === 0));

  const sharedAxes = isHours ? (
    <>
      <CartesianGrid stroke="none" vertical={false} horizontal={false} />
      <XAxis
        dataKey="hour"
        tick={{ fill: 'var(--text-faint)', fontSize: 12 }}
        axisLine={false}
        tickLine={false}
        tickFormatter={formatHour}
        interval={2}
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
    </>
  ) : (
    <>
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
    </>
  );

  return (
    <div className="chart-card">
      <div className="chart-card-head">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div className="chart-title">Clicks</div>
          <div className="metric-toggle" role="tablist">
            <button
              role="tab"
              aria-selected={!isHours}
              className={`metric-toggle-btn${!isHours ? ' active' : ''}`}
              onClick={() => setViewTab('days')}
            >
              Days
            </button>
            <button
              role="tab"
              aria-selected={isHours}
              className={`metric-toggle-btn${isHours ? ' active' : ''}`}
              onClick={() => setViewTab('hours')}
            >
              Hours
            </button>
          </div>
        </div>
        <div className="chart-head-right">
          <ChartTypeToggle chartType={chartType} onChartTypeChange={setChartType} />
          <RangeDropdown range={range} onRangeChange={onRangeChange} />
        </div>
      </div>

      {isEmpty ? (
        <div className="empty-state">
          <div className="empty-title">No click data yet</div>
          <div className="empty-desc">Share your link to start seeing clicks here.</div>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={280}>
          {chartType === 'bar' ? (
            <BarChart data={activeData} margin={{ top: 12, right: 8, left: -18, bottom: 0 }}>
              {sharedAxes}
              <Tooltip
                content={isHours ? <CustomHourTooltip /> : <CustomTooltip />}
                cursor={{ fill: 'var(--accent-tint)' }}
              />
              <Bar
                dataKey="clicks"
                fill="#6366F1"
                radius={[4, 4, 0, 0]}
                maxBarSize={isHours ? 24 : 40}
              />
            </BarChart>
          ) : (
            <AreaChart data={activeData} margin={{ top: 12, right: 8, left: -18, bottom: 0 }}>
              <defs>
                <linearGradient id="clicksGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366F1" stopOpacity={0.22} />
                  <stop offset="95%" stopColor="#6366F1" stopOpacity={0} />
                </linearGradient>
              </defs>
              {sharedAxes}
              <Tooltip
                content={isHours ? <CustomHourTooltip /> : <CustomTooltip />}
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
          )}
        </ResponsiveContainer>
      )}
    </div>
  );
}
