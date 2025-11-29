import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@lesson-mode': path.resolve(__dirname, '../shared/lesson-mode/src'),
      '@lesson-browser': path.resolve(__dirname, '../shared/lesson-browser/src'),
      '@lesson-api': path.resolve(__dirname, '../shared/lesson-api/src'),
      '@lesson-ui': path.resolve(__dirname, './src/components/ui'),
      '@tauri-apps/api': path.resolve(__dirname, './node_modules/@tauri-apps/api'),
    },
  },
  clearScreen: false,
  server: {
    port: 1420,
    strictPort: true,
    host: '0.0.0.0', // Listen on all interfaces for Android emulator access
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('proxy error', err);
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log('Sending Request to the Target:', req.method, req.url);
          });
          proxy.on('proxyRes', (proxyRes, req, _res) => {
            console.log('Received Response from the Target:', proxyRes.statusCode, req.url);
          });
        },
      },
    },
    watch: {
      ignored: ['**/src-tauri/**'],
    },
  },
  envPrefix: ['VITE_', 'TAURI_'],
  build: {
    target: process.env.TAURI_PLATFORM == 'windows' ? 'chrome105' : 'safari13',
    minify: !process.env.TAURI_DEBUG ? 'esbuild' : false,
    sourcemap: !!process.env.TAURI_DEBUG,
  },
});
