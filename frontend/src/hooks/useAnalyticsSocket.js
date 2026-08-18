import { useEffect, useRef } from 'react';

export function useAnalyticsSocket(code, onNewClick) {
  const onNewClickRef = useRef(onNewClick);
  onNewClickRef.current = onNewClick;

  useEffect(() => {
    if (!code) return;

    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const ws = new WebSocket(`${protocol}://${window.location.host}/v1/ws/analytics/${code}`);

    ws.onmessage = (event) => {
      try {
        const click = JSON.parse(event.data);
        onNewClickRef.current(click);
      } catch {
        // ignore malformed messages
      }
    };

    ws.onerror = () => ws.close();

    return () => ws.close();
  }, [code]);
}
