import { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';

function Logo() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="#FFFFFF" aria-hidden="true">
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
    </svg>
  );
}

function ChartIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <line x1="18" y1="20" x2="18" y2="10" />
      <line x1="12" y1="20" x2="12" y2="4" />
      <line x1="6" y1="20" x2="6" y2="14" />
    </svg>
  );
}

export default function NavBar() {
  const [open, setOpen] = useState(false);
  const [value, setValue] = useState('');
  const inputRef = useRef(null);
  const wrapperRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

  // Close on click outside
  useEffect(() => {
    if (!open) return;
    function handleClick(e) {
      if (!wrapperRef.current?.contains(e.target)) handleClose();
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [open]);

  // Close on Escape
  useEffect(() => {
    if (!open) return;
    function handleKey(e) {
      if (e.key === 'Escape') handleClose();
    }
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [open]);

  function extractCode(input) {
    const trimmed = input.trim();
    try {
      const url = new URL(trimmed);
      return url.pathname.replace(/^\//, '');
    } catch {
      return trimmed.replace(/^\//, '');
    }
  }

  function handleSubmit(e) {
    e.preventDefault();
    const code = extractCode(value);
    if (!code) return;
    setOpen(false);
    setValue('');
    navigate(`/analytics/${encodeURIComponent(code)}`);
  }

  function handleClose() {
    setOpen(false);
    setValue('');
  }

  return (
    <nav className="navbar" role="navigation" aria-label="Main navigation">
      <div className="container">
        <div className="navbar-inner">
          <Link to="/" className="navbar-logo" aria-label="Snip — home">
            <div className="navbar-logo-icon" aria-hidden="true">
              <Logo />
            </div>
            snip
          </Link>

          <div className="track-wrapper" ref={wrapperRef}>
            {!open ? (
              <button className="track-trigger" onClick={() => setOpen(true)}>
                <ChartIcon />
                Track a link
              </button>
            ) : (
              <form className="track-inline" onSubmit={handleSubmit}>
                <input
                  ref={inputRef}
                  className="track-inline-input"
                  type="text"
                  placeholder="Short URL or code…"
                  value={value}
                  onChange={e => setValue(e.target.value)}
                  aria-label="Short URL or code"
                />
                <button className="track-inline-go" type="submit" disabled={!value.trim()} aria-label="Track link">
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <line x1="5" y1="12" x2="19" y2="12" />
                    <polyline points="12 5 19 12 12 19" />
                  </svg>
                </button>
              </form>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
