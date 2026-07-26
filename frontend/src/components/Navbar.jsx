import { Link } from 'react-router-dom';

function Logo() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="#A8D520" aria-hidden="true">
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
    </svg>
  );
}

export default function NavBar() {
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

          <div className="navbar-nav">
            <Link to="/dashboard" className="nav-link">
              Recent links
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}

