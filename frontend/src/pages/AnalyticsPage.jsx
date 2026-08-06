import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import StatsCard from '../components/StatsCard.jsx';
import ClicksChart from '../components/ClicksChart.jsx';
import DistributionBar from '../components/DistributionBar.jsx';
import DonutChart from '../components/DonutChart.jsx';
import LocationChart from '../components/LocationChart.jsx';
import PeakHoursChart from '../components/PeakHoursChart.jsx';
import { getUrlStats } from '../api/api.js';
import { useClipboard } from '../hooks/useClipboard.js';

function BackIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M19 12H5M12 5l-7 7 7 7" />
    </svg>
  );
}

function ClickIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M15 15l-2 5L9 9l11 4-5 2z" />
      <path d="M22 22l-5-5" />
    </svg>
  );
}

function UsersIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  );
}

function TodayIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
      <line x1="16" y1="2" x2="16" y2="6" />
      <line x1="8" y1="2" x2="8" y2="6" />
      <line x1="3" y1="10" x2="21" y2="10" />
    </svg>
  );
}

function AvgIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
    </svg>
  );
}

function CopyIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M20 6L9 17l-5-5" />
    </svg>
  );
}

function ExternalLinkIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
      <polyline points="15 3 21 3 21 9" />
      <line x1="10" y1="14" x2="21" y2="3" />
    </svg>
  );
}

function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function formatTime(dateStr) {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
}

export default function AnalyticsPage() {
  const { code } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { copied, copy } = useClipboard();

  useEffect(() => {
    setLoading(true);
    setError(null);
    getUrlStats(code)
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [code]);

  if (loading) {
    return (
      <div className="analytics-page">
        <div className="container">
          <div className="empty-state">
            <div className="spinner spinner-lg" role="status" aria-label="Loading analytics…" style={{ margin: '0 auto' }} />
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="analytics-page">
        <div className="container">
          <Link to="/" className="analytics-back">
            <BackIcon /> Back
          </Link>
          <div className="form-error" role="alert">{error}</div>
        </div>
      </div>
    );
  }

  const { link, summary, clicks_by_day, peak_hours, by_device, by_browser, by_os, by_country, by_city } = data;

  return (
    <div className="analytics-page">
      <div className="container">
        <Link to="/" className="analytics-back" aria-label="Back to home">
          <BackIcon /> Back
        </Link>

        {/* Link hero section */}
        <div className="dash-hero">
          <div className="dash-hero-left">
            <div className="dash-short-url">
              <a href={link.short_url} target="_blank" rel="noopener noreferrer" className="dash-short-link">
                {link.short_url}
                <ExternalLinkIcon />
              </a>
            </div>
            <div className="dash-long-url">{link.long_url}</div>
            <div className="dash-meta">Created {formatDate(link.created_at)}</div>
          </div>
          <div className="dash-hero-actions">
            <button
              className={`btn-copy-dash${copied ? ' copied' : ''}`}
              onClick={() => copy(link.short_url)}
            >
              {copied ? <CheckIcon /> : <CopyIcon />}
              {copied ? 'Copied!' : 'Copy Link'}
            </button>
          </div>
        </div>

        {/* Stats grid */}
        <div className="stats-row stats-row-4">
          <StatsCard icon={<ClickIcon />} value={summary.total_clicks.toLocaleString()} label="Total clicks" />
          <StatsCard icon={<UsersIcon />} value={summary.unique_clicks.toLocaleString()} label="Unique visitors" />
          <StatsCard icon={<TodayIcon />} value={summary.clicks_today.toLocaleString()} label="Today" />
          <StatsCard icon={<AvgIcon />} value={summary.avg_clicks_per_day.toLocaleString()} label="Avg / day" />
        </div>

        {/* Charts row */}
        <ClicksChart data={clicks_by_day} />
        <PeakHoursChart data={peak_hours} />

        {/* Donut charts row */}
        <div className="donut-row">
          <LocationChart countryData={by_country} cityData={by_city} />
          <DonutChart title="Device" data={by_device} />
        </div>


      </div>
    </div>
  );
}
