import { Link } from 'react-router-dom';
import { useClipboard } from '../hooks/useClipboard.js';

function CheckIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M20 6L9 17l-5-5" />
    </svg>
  );
}

function CopyIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
    </svg>
  );
}

function BarIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <line x1="18" y1="20" x2="18" y2="10" />
      <line x1="12" y1="20" x2="12" y2="4" />
      <line x1="6" y1="20" x2="6" y2="14" />
    </svg>
  );
}

export default function UrlResult({ result, originalUrl }) {
  const { short_url, code } = result;
  const { copied, copy } = useClipboard();

  return (
    <div className="url-result" role="region" aria-label="Shortened URL result">
      <div className="url-result-header">
        <div className="url-result-dot" aria-hidden="true" />
        <span>link ready</span>
      </div>

      <div className="url-result-body">
        <div className="url-result-short">
          <div className="short-code-display" aria-label={`Shortened URL: ${short_url}`}>
            {short_url}
          </div>

          <div className="url-result-actions">
            <button
              className={`btn-copy${copied ? ' copied' : ''}`}
              onClick={() => copy(short_url)}
              aria-label={copied ? 'Copied to clipboard' : 'Copy short URL to clipboard'}
            >
              {copied ? <CheckIcon /> : <CopyIcon />}
              {copied ? 'Copied' : 'Copy'}
            </button>

            <Link
              to={`/analytics/${code}`}
              className="btn-analytics"
              aria-label={`View analytics for /${code}`}
            >
              <BarIcon />
              Analytics
            </Link>
          </div>
        </div>

        <div className="url-result-original">
          → <a href={short_url} target="_blank" rel="noopener noreferrer">{short_url}</a>
        </div>
      </div>
    </div>
  );
}
