import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// Without this file Vite never loads the React plugin, so JSX falls back
// to the classic React.createElement transform — and `React is not defined`
// at runtime because nothing imports it. The plugin also enables the
// automatic JSX runtime + fast refresh, and proxies API calls to the
// backend during development (avoids CORS setup for `npm run dev`).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
      // ponytail: same /admin prefix serves the SPA route (/admin) and the
      // backend API (/admin/jobs). Browser navigations send Accept: text/html
      // so they fall through to index.html; fetch() API calls get proxied.
      '/admin': {
        target: 'http://localhost:8000',
        bypass: (req) => (req.headers.accept?.includes('text/html') ? '/index.html' : undefined),
      },
    },
  },
});
