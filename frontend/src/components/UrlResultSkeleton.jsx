export default function UrlResultSkeleton() {
  return (
    <div className="url-result url-result-skeleton" role="status" aria-label="Generating your short link…">
      {/* Header row — matches .url-result-header */}
      <div className="url-result-header">
        <div className="skel-block" style={{ width: 7, height: 7, borderRadius: '50%' }} />
        <div className="skel-block" style={{ width: 60, height: 10, borderRadius: 4 }} />
      </div>

      {/* Body — matches .url-result-body */}
      <div className="url-result-body">
        {/* Short URL row */}
        <div className="url-result-short">
          {/* Mimics .short-code-display text */}
          <div className="skel-block" style={{ width: 200, height: 24, borderRadius: 6 }} />

          {/* Mimics action buttons */}
          <div style={{ display: 'flex', gap: 8 }}>
            <div className="skel-block" style={{ width: 80, height: 34, borderRadius: 10 }} />
            <div className="skel-block" style={{ width: 96, height: 34, borderRadius: 10 }} />
          </div>
        </div>

        {/* Original URL row — matches .url-result-original */}
        <div className="url-result-original">
          <div className="skel-block" style={{ width: 160, height: 13, borderRadius: 4 }} />
        </div>
      </div>
    </div>
  );
}
