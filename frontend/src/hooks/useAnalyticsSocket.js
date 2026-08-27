import { useEffect, useRef } from 'react';

export function useAnalyticsSocket(code, onSnapshot, enabled = true) {
  const onSnapshotRef = useRef(onSnapshot);
  onSnapshotRef.current = onSnapshot;

  useEffect(() => {
    if (!code || !enabled) return;

    const url = `/v1/analytics/live/${code}`;
    const es = new EventSource(url);

    es.addEventListener('click', (event) => {
      try {
        const snapshot = JSON.parse(event.data);
        onSnapshotRef.current(snapshot);
      } catch {
        // ignore malformed messages
      }
    });

    es.onerror = () => {
      // EventSource reconnects automatically — no manual backoff needed
    };

    return () => es.close();
  }, [code, enabled]);
}
