import { useState } from 'react';
import UrlForm from '../components/UrlForm.jsx';

const EXAMPLES = [
  { label: 'google.com/maps/place...', url: 'https://www.google.com/maps/place/Eiffel+Tower/@48.8583701,2.2944813,17z' },
  { label: 'en.wikipedia.org/wiki/Art...', url: 'https://en.wikipedia.org/wiki/Artificial_intelligence' },
  { label: 'openai.com/index/advancing...', url: 'https://openai.com/index/advancing-the-price-performance-frontier-with-gpt-5-6/' },
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

          <div className="hero-pills">
            {EXAMPLES.map((ex) => (
              <button
                key={ex.url}
                className="hero-pill"
                onClick={() => setPrefillUrl(ex.url)}
                type="button"
              >
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
                  <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
                </svg>
                {ex.label}
              </button>
            ))}
          </div>

        </div>
      </section>
    </main>
  );
}
