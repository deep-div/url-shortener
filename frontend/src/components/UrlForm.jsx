import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { shortenUrl } from '../api/api.js';

function LinkIcon() {
  return (
    <svg
      className="url-input-icon"
      width="17" height="17" viewBox="0 0 24 24"
      fill="none" stroke="currentColor" strokeWidth="2"
      strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"
    >
      <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
      <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
    </svg>
  );
}

export default function UrlForm({ defaultUrl = '' }) {
  const [url, setUrl] = useState(defaultUrl);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (defaultUrl) setUrl(defaultUrl);
  }, [defaultUrl]);

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
            <LinkIcon />
            <input
              className="url-input"
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Paste your long URL here..."
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
            {loading ? 'Shortening…' : 'Shorten →'}
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
