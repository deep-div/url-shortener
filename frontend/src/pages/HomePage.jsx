import { useState } from 'react';
import UrlForm from '../components/UrlForm.jsx';

function ChainIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
      <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
    </svg>
  );
}

function BarChartIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <line x1="18" y1="20" x2="18" y2="10" />
      <line x1="12" y1="20" x2="12" y2="4" />
      <line x1="6" y1="20" x2="6" y2="14" />
    </svg>
  );
}

function ShieldCheckIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      <polyline points="9 12 11 14 15 10" />
    </svg>
  );
}

function WorldIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="10" />
      <line x1="2" y1="12" x2="22" y2="12" />
      <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
    </svg>
  );
}

const EXAMPLES = [
  { label: 'youtube.com/watch?v=dQw4...', url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ' },
  { label: 'github.com/openai/openai-py...', url: 'https://github.com/openai/openai-python' },
  { label: 'amazon.in/dp/B09X7CR...', url: 'https://www.amazon.in/dp/B09X7CRKRZ' },
];

export default function HomePage() {
  const [prefillUrl, setPrefillUrl] = useState('');

  return (
    <main className="home-main">
      <section className="hero">
        <div className="container">

          <h1 className="hero-title">
            <span className="hero-line-1">Short links</span>
            <span className="hero-line-2">
              Powerful <span className="hero-accent">insights</span>
            </span>
          </h1>

          <UrlForm defaultUrl={prefillUrl} />

          <div className="hero-examples">
            <span className="hero-examples-label">Examples:</span>
            {EXAMPLES.map((ex) => (
              <button
                key={ex.url}
                className="hero-example-btn"
                onClick={() => setPrefillUrl(ex.url)}
                type="button"
              >
                {ex.label}
              </button>
            ))}
          </div>

        </div>
      </section>

      <section className="stats-bar">
        <div className="container">
          <div className="hero-bottom-stats">
            <div className="hero-stat-item">
              <div className="hero-stat-icon purple"><ChainIcon /></div>
              <div className="hero-stat-text">
                <div className="hero-stat-value">2.8M+</div>
                <div className="hero-stat-label">Links Created</div>
              </div>
            </div>
            <div className="hero-stat-item">
              <div className="hero-stat-icon blue"><BarChartIcon /></div>
              <div className="hero-stat-text">
                <div className="hero-stat-value">42M+</div>
                <div className="hero-stat-label">Total Clicks</div>
              </div>
            </div>
            <div className="hero-stat-item">
              <div className="hero-stat-icon green"><ShieldCheckIcon /></div>
              <div className="hero-stat-text">
                <div className="hero-stat-value">99.99%</div>
                <div className="hero-stat-label">Uptime</div>
              </div>
            </div>
            <div className="hero-stat-item">
              <div className="hero-stat-icon orange"><WorldIcon /></div>
              <div className="hero-stat-text">
                <div className="hero-stat-value">138+</div>
                <div className="hero-stat-label">Countries</div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
