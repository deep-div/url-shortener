import { useState } from 'react';
import {
  AreaChart, Area,
  BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import { formatCompactNumber } from '../utils/format.js';

function formatDay(val) {
  // "2026-08-05" -> "Aug 5"
  const d = new Date(`${val}T00:00:00`);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

// Same K / L / Cr compact scheme used on the stat cards, so the chart axis
// and the cards below it never disagree on how a number is abbreviated.
function formatYAxis(val) {
  return formatCompactNumber(val);
}

// Rounds up to a "nice" 1/2/5-times-a-power-of-ten number so the axis top
// isn't the raw data max (which produces an uneven trailing tick gap).
function niceCeil(value) {
  if (!value || value <= 0) return 10;
  const exponent = Math.floor(Math.log10(value));
  const magnitude = 10 ** exponent;
  const fraction = value / magnitude;
  const niceFraction = fraction <= 1 ? 1 : fraction <= 2 ? 2 : fraction <= 5 ? 5 : 10;
  return niceFraction * magnitude;
}

// Builds an evenly-spaced tick set [0, step, 2*step, 3*step, 4*step] whose
// top always matches the axis domain max.
function getYAxisTicks(maxValue) {
  const domainMax = niceCeil(maxValue);
  const step = domainMax / 4;
  return { domainMax, ticks: [0, step, step * 2, step * 3, domainMax] };
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

export default function ClicksChart({ data, peakHours }) {
  const [chartType, setChartType] = useState('area');
  const [viewTab, setViewTab] = useState('days');

  const hoursData = peakHours
    ? Array.from({ length: 24 }, (_, i) => ({ hour: String(i), clicks: peakHours[String(i)] ?? 0 }))
    : [];

  const isHours = viewTab === 'hours';
  const activeData = isHours ? hoursData : data;
  const isEmpty = !activeData || activeData.length === 0 || (isHours && activeData.every(d => d.clicks === 0));

  const maxClicks = activeData?.length ? Math.max(...activeData.map((d) => d.clicks ?? 0)) : 0;
  const { domainMax, ticks: yTicks } = getYAxisTicks(maxClicks);

  const sharedAxes = isHours ? (
    <>
      <CartesianGrid stroke="none" vertical={false} horizontal={false} />
      <XAxis
        dataKey="hour"
        tick={{ fill: 'var(--text-muted)', fontSize: 12 }}
        axisLine={false}
        tickLine={false}
        tickFormatter={formatHour}
        interval={2}
        padding={{ left: 12, right: 12 }}
      />
      <YAxis
        tick={{ fill: 'var(--text-muted)', fontSize: 12 }}
        axisLine={false}
        tickLine={false}
        allowDecimals={false}
        tickFormatter={formatYAxis}
        domain={[0, domainMax]}
        ticks={yTicks}
        width={56}
      />
    </>
  ) : (
    <>
      <CartesianGrid stroke="none" vertical={false} horizontal={false} />
      <XAxis
        dataKey="date"
        tick={{ fill: 'var(--text-muted)', fontSize: 12 }}
        axisLine={false}
        tickLine={false}
        tickFormatter={formatDay}
        padding={{ left: 12, right: 12 }}
      />
      <YAxis
        tick={{ fill: 'var(--text-muted)', fontSize: 12 }}
        axisLine={false}
        tickLine={false}
        allowDecimals={false}
        tickFormatter={formatYAxis}
        domain={[0, domainMax]}
        ticks={yTicks}
        width={56}
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
            <BarChart data={activeData} margin={{ top: 12, right: 8, left: 0, bottom: 0 }}>
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
            <AreaChart data={activeData} margin={{ top: 12, right: 8, left: 0, bottom: 0 }}>
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
