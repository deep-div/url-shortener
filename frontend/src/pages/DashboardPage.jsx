import { useEffect, useState } from 'react';
import StatsCard from '../components/StatsCard.jsx';
import TopUrlsList from '../components/TopUrlsList.jsx';
import { getDashboard } from '../api/api.js';

function LinkIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
      <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
    </svg>
  );
}

function ActivityIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
    </svg>
  );
}

function ClockIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </svg>
  );
}

export default function DashboardPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getDashboard()
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="dashboard-page">
        <div className="container">
          <div className="empty-state">
            <div className="spinner spinner-lg" role="status" aria-label="Loading dashboard…" style={{ margin: '0 auto' }} />
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-page">
        <div className="container">
          <div className="form-error" role="alert">{error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-page">
      <div className="container">
        <div className="dashboard-header">
          <h1 className="dashboard-title">Dashboard</h1>
          <p className="dashboard-subtitle">Your link performance at a glance.</p>
        </div>

        <div className="dashboard-stats-row">
          <StatsCard
            icon={<LinkIcon />}
            value={data.total_urls.toLocaleString()}
            label="Total URLs"
          />
          <StatsCard
            icon={<ActivityIcon />}
            value={data.total_clicks.toLocaleString()}
            label="Total clicks"
          />
          <StatsCard
            icon={<ClockIcon />}
            value={data.clicks_today.toLocaleString()}
            label="Clicks today"
          />
        </div>

        <div className="section-header">
          <div>
            <div className="section-title">Top links</div>
            <div className="section-subtitle">Ranked by total clicks</div>
          </div>
        </div>

        <TopUrlsList urls={data.top_urls} />
      </div>
    </div>
  );
}
