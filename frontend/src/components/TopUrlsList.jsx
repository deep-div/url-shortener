import { Link } from 'react-router-dom';

function BarIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <line x1="18" y1="20" x2="18" y2="10" />
      <line x1="12" y1="20" x2="12" y2="4" />
      <line x1="6" y1="20" x2="6" y2="14" />
    </svg>
  );
}

/**
 * Table of top-performing shortened URLs.
 * @param {{ urls: Array<{ code: string, clicks: number }> }} props
 */
export default function TopUrlsList({ urls }) {
  if (!urls || urls.length === 0) {
    return (
      <div className="top-urls-card">
        <div className="empty-state">
          <div className="empty-title">No links yet</div>
          <div className="empty-desc">Shorten your first URL to see it here.</div>
        </div>
      </div>
    );
  }

  return (
    <div className="top-urls-card" role="table" aria-label="Top URLs by clicks">
      <div className="table-header" role="row">
        <span role="columnheader">Code</span>
        <span role="columnheader">Clicks</span>
        <span role="columnheader" aria-hidden="true" />
      </div>
      {urls.map(({ code, clicks }) => (
        <div key={code} className="table-row" role="row">
          <span className="table-code" role="cell">/{code}</span>
          <span className="table-clicks" role="cell">{clicks.toLocaleString()}</span>
          <Link
            to={`/analytics/${code}`}
            className="table-action"
            role="cell"
            aria-label={`View analytics for /${code}`}
          >
            <BarIcon />
            View
          </Link>
        </div>
      ))}
    </div>
  );
}
