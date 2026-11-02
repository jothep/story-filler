import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  base: '/story-filler/', // Shared by GitHub Pages, the router and local frontends.
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/setupTests.js',
  },
  server: {
    host: '0.0.0.0',
    port: 5173,

    // Forward local API, admin and media requests to the backend/Ingress.
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
      '/admin': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
      '/static': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
      '/media': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
    },
  },
});
