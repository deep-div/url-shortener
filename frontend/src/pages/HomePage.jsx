import { useEffect, useState } from 'react';
import UrlForm from '../components/UrlForm.jsx';
import StatsCard from '../components/StatsCard.jsx';
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

export default function HomePage() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    getDashboard().then(setStats).catch(() => {});
  }, []);

  return (
    <main>
      <section className="hero">
        <div className="container">
          <h1 className="hero-title">
            <span className="hero-line-1">Shorten links</span>
            <span className="hero-line-2">Watch the clicks</span>
          </h1>

          <p className="hero-subtitle">
            Turn long URLs into snappy ones and get a live dashboard of clicks,
            referrers, and devices, all in one place.
          </p>

          <UrlForm />

          <div className="feature-pills" aria-label="Key features">
            <div className="feature-pill">
              <div className="feature-pill-icon" aria-hidden="true">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                  <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
                </svg>
              </div>
              Live analytics
            </div>
            <div className="feature-pill">
              <div className="feature-pill-icon" aria-hidden="true">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                </svg>
              </div>
              Click tracking
            </div>
            <div className="feature-pill">
              <div className="feature-pill-icon" aria-hidden="true">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
                </svg>
              </div>
              Instant redirect
            </div>
          </div>
        </div>
      </section>

      {stats && (
        <section aria-label="Overall stats">
          <div className="container">
            <div className="stats-row">
              <StatsCard
                icon={<LinkIcon />}
                value={stats.total_urls.toLocaleString()}
                label="Links shortened"
              />
              <StatsCard
                icon={<ActivityIcon />}
                value={stats.total_clicks.toLocaleString()}
                label="Total clicks tracked"
              />
              <StatsCard
                icon={<ClockIcon />}
                value={stats.clicks_today.toLocaleString()}
                label="Clicks today"
              />
            </div>
          </div>
        </section>
      )}
    </main>
  );
}
