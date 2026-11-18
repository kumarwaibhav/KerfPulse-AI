import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    strictPort: true,
    proxy: { '/api': 'http://127.0.0.1:8000', '/healthz': 'http://127.0.0.1:8000' },
  },
  preview: { host: '127.0.0.1', strictPort: true },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules/zrender/')) return 'canvas';
          if (id.includes('node_modules/echarts/')) return 'charts';
          if (id.includes('node_modules/react-dom/') || id.includes('node_modules/react/')) return 'react';
        },
      },
    },
  },
});
