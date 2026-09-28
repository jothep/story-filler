// vite.config.js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/story-filler/',  // Shared by GitHub Pages, the router and local frontends.
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/setupTests.js',
  },
  server: {
    host: '0.0.0.0',
    port: 5173,

    // --- 👇 在这里添加你的 proxy 配置 ---
    proxy: {
      // 代理 /api/... 的请求
      // 这对应你的 ingress.yaml
      '/api': {
        target: 'http://127.0.0.1:8080', // 你的 K8s 隧道入口
        changeOrigin: true, // 必须
      },
      // 代理 /admin/... 的请求
      '/admin': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
      // 代理 /static/... 的请求
      '/static': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
      // (推荐) 代理你的媒体文件，比如 word.image
      // 我猜你的 Django MEDIA_URL 是 /media/
      '/media': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
    },
    // --- 👆 proxy 配置结束 ---
  },
});
