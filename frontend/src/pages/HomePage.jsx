import UrlForm from '../components/UrlForm.jsx';

export default function HomePage() {
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
        </div>
      </section>
    </main>
  );
}
