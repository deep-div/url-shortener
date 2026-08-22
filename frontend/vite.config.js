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
      '/v1': { target: 'http://127.0.0.1:8000' },
      '/health': 'http://127.0.0.1:8000',
    },
  },
})
