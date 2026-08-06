import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { shortenUrl } from '../api/api.js';

function ArrowIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M5 12h14M12 5l7 7-7 7" />
    </svg>
  );
}

export default function UrlForm() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    const trimmed = url.trim();
    if (!trimmed) return;

    setLoading(true);
    setError(null);

    try {
      const data = await shortenUrl(trimmed);
      navigate(`/analytics/${data.code}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="url-form">
      <form onSubmit={handleSubmit} noValidate>
        <div className="url-form-inner">
          <div className="url-input-wrap">
            <input
              className="url-input"
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com/really/long/url"
              required
              aria-label="URL to shorten"
              autoComplete="url"
              spellCheck={false}
            />
          </div>
          <button
            type="submit"
            className="url-form-btn"
            disabled={loading || !url.trim()}
            aria-busy={loading}
          >
            <ArrowIcon />
            Shorten
          </button>
        </div>
      </form>

      {error && (
        <div className="form-error" role="alert">
          {error}
        </div>
      )}
    </div>
  );
}
