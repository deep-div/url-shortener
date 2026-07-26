import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import StatsCard from '../components/StatsCard.jsx';
import ClicksChart from '../components/ClicksChart.jsx';
import DistributionBar from '../components/DistributionBar.jsx';
import { getUrlStats } from '../api/api.js';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

function BackIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M19 12H5M12 5l-7 7 7 7" />
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

export default function AnalyticsPage() {
  const { code } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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

  return (
    <div className="analytics-page">
      <div className="container">
        <Link to="/" className="analytics-back" aria-label="Back to home">
          <BackIcon /> Back
        </Link>

        <div className="analytics-header">
          <div className="analytics-code" aria-label={`Short code: ${code}`}>/{code}</div>
          <div className="analytics-url-label">{BASE_URL}/{code}</div>
        </div>

        <div className="analytics-stats-row">
          <StatsCard
            icon={<ActivityIcon />}
            value={data.total_clicks.toLocaleString()}
            label="Total clicks"
          />
          <StatsCard
            icon={<UsersIcon />}
            value={data.unique_clicks.toLocaleString()}
            label="Unique visitors"
          />
        </div>

        <ClicksChart data={data.clicks_by_day} />

        <div className="distribution-section">
          <DistributionBar title="Device" data={data.by_device} />
          <DistributionBar title="Browser" data={data.by_browser} />
          <DistributionBar title="Operating System" data={data.by_os} />
          <DistributionBar title="Country" data={data.by_country} />
          <DistributionBar title="Referrer" data={data.by_referrer} />
        </div>
      </div>
    </div>
  );
}
