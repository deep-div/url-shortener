import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import ClicksChart from '../components/ClicksChart.jsx';
import DonutChart from '../components/DonutChart.jsx';
import MetricBars from '../components/MetricBars.jsx';
import StatsSummaryBar from '../components/StatsSummaryBar.jsx';
import { getUrlStats } from '../api/api.js';
import { useClipboard } from '../hooks/useClipboard.js';
import { useAnalyticsSocket } from '../hooks/useAnalyticsSocket.js';

function BackIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M19 12H5M12 5l-7 7 7 7" />
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
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <line x1="7" y1="17" x2="17" y2="7" />
      <polyline points="7 7 17 7 17 17" />
    </svg>
  );
}

function getRangeDates(value) {
  const today = new Date();
  const fmt = (d) => d.toISOString().split('T')[0];
  const ago = (n) => { const d = new Date(today); d.setDate(d.getDate() - n); return d; };
  if (value === 'today')     return { from: fmt(today),    to: fmt(today) };
  if (value === 'yesterday') return { from: fmt(ago(1)),   to: fmt(ago(1)) };
  if (value === '7d')        return { from: fmt(ago(6)),   to: fmt(today) };
  if (value === '14d')       return { from: fmt(ago(13)),  to: fmt(today) };
  if (value === '30d')       return { from: fmt(ago(29)),  to: fmt(today) };
  if (value === '90d')       return { from: fmt(ago(89)),  to: fmt(today) };
  return {};
}

export default function AnalyticsPage() {
  const { code } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [range, setRange] = useState('all');
  const { copied, copy } = useClipboard();

  useEffect(() => {
    setLoading(true);
    setError(null);
    getUrlStats(code, getRangeDates(range))
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [code, range]);

  useAnalyticsSocket(code, (snapshot) => {
    setData((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        summary: snapshot.summary,
        by_country: snapshot.by_country,
        by_city: snapshot.by_city,
        by_device: snapshot.by_device,
        by_browser: snapshot.by_browser,
        by_os: snapshot.by_os,
      };
    });
  });

  if (loading) {
    return (
      <div className="analytics-page">
        <div className="container">
          <div className="skel-block" style={{ width: 60, height: 14, borderRadius: 6, marginBottom: 24 }} />
          <div className="skel-block" style={{ height: 96, borderRadius: 18, marginBottom: 24 }} />
          <div className="skel-block" style={{ height: 88, borderRadius: 18, marginBottom: 24 }} />
          <div className="skel-block" style={{ height: 340, borderRadius: 18, marginBottom: 24 }} />
          <div className="analytics-grid-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="skel-block" style={{ height: 360, borderRadius: 18 }} />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    const isNotFound = error.startsWith('No analytics found');
    return (
      <div className="analytics-page">
        <div className="container">
          <Link to="/" className="analytics-back">
            <BackIcon /> Back
          </Link>
          <div className="error-page">
            <div className="error-page-icon">
              {isNotFound ? (
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <circle cx="11" cy="11" r="8" />
                  <line x1="21" y1="21" x2="16.65" y2="16.65" />
                  <line x1="11" y1="8" x2="11" y2="11" />
                  <line x1="11" y1="14" x2="11.01" y2="14" />
                </svg>
              ) : (
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="8" x2="12" y2="12" />
                  <line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
              )}
            </div>
            <div className="error-page-title">
              {isNotFound ? 'Link not found' : 'Something went wrong'}
            </div>
            <Link to="/" className="error-page-btn">
              Shorten a new link
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const { link, summary, clicks_by_day, peak_hours, by_device, by_browser, by_country, by_city } = data;

  return (
    <div className="analytics-page">
      <div className="container">
        <Link to="/" className="analytics-back" aria-label="Back to home">
          <BackIcon /> Back
        </Link>

        {/* Link hero — short url, long url, created date */}
        <div className="dash-hero">
          <div className="dash-hero-left">
            <div className="dash-short-url">
              <a href={link.short_url} target="_blank" rel="noopener noreferrer" className="dash-short-link">
                {link.short_url}
                <ExternalLinkIcon />
              </a>
            </div>
            <div className="dash-long-url">{link.long_url}</div>
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

        {/* Stats summary */}
        <StatsSummaryBar summary={summary} />

        {/* Clicks over time */}
        <ClicksChart data={clicks_by_day} peakHours={peak_hours} range={range} onRangeChange={setRange} />

        {/* Locations · Devices · Browsers */}
        <div className="analytics-grid-3">
          <MetricBars
            tabs={[
              { label: 'Countries', data: by_country },
              { label: 'Cities', data: by_city },
            ]}
            scroll
          />
          <DonutChart title="Devices" data={by_device} />
          <MetricBars title="Top Browsers" data={by_browser} scroll />
        </div>
      </div>
    </div>
  );
}
