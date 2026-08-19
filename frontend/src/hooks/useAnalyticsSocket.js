import { useEffect, useRef } from 'react';

export function useAnalyticsSocket(code, onNewClick) {
  const onNewClickRef = useRef(onNewClick);
  onNewClickRef.current = onNewClick;

  useEffect(() => {
    if (!code) return;

    let ws;
    let attempt = 0;
    let destroyed = false;

    function connect() {
      if (destroyed) return;
      const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
      ws = new WebSocket(`${protocol}://${window.location.host}/v1/ws/analytics/${code}`);

      ws.onmessage = (event) => {
        // Server sends "ping" frames to keep the connection alive — ignore them
        if (event.data === 'ping') return;
        try {
          const click = JSON.parse(event.data);
          onNewClickRef.current(click);
        } catch {
          // ignore malformed messages
        }
      };

      ws.onopen = () => {
        attempt = 0;
      };

      ws.onclose = () => {
        if (destroyed) return;
        // Exponential backoff: 500ms, 1s, 2s, 4s … capped at 30s
        const delay = Math.min(500 * 2 ** attempt, 30_000);
        attempt += 1;
        setTimeout(connect, delay);
      };

      ws.onerror = () => ws.close();
    }

    connect();

    return () => {
      destroyed = true;
      ws?.close();
    };
  }, [code]);
}
