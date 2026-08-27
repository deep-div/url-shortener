import { defineConfig } from 'vite'
import react, { reactCompilerPreset } from '@vitejs/plugin-react'
import babel from '@rolldown/plugin-babel'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    babel({ presets: [reactCompilerPreset()] })
  ],
  server: {
    port: 4000,
    proxy: {
      '/v1': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        // Backend restarts (e.g. uvicorn --reload) drop in-flight SSE/HTTP
        // connections with ECONNRESET. Without an 'error' listener here,
        // Vite's underlying http-proxy throws and crashes the whole dev
        // server. Swallow it instead — the browser's EventSource/fetch will
        // retry on its own once the backend is back up.
        configure: (proxy) => {
          proxy.on('error', (err, _req, res) => {
            console.error('[vite proxy] error:', err.message);
            if (res && !res.headersSent) {
              res.writeHead(502, { 'Content-Type': 'text/plain' });
            }
            if (res && !res.writableEnded) {
              res.end('Bad gateway');
            }
          });
        },
      },
      '/health': 'http://127.0.0.1:8000',
    },
  },
})
