import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@lesson-mode': path.resolve(__dirname, '../../shared/lesson-mode/src'),
      '@lesson-browser': path.resolve(__dirname, '../../shared/lesson-browser/src'),
      '@lesson-api': path.resolve(__dirname, '../../shared/lesson-api/src'),
      '@lesson-ui': path.resolve(__dirname, './src/components/ui'),
      // Ensure all shared package dependencies resolve from frontend's node_modules
      'lucide-react': path.resolve(__dirname, './node_modules/lucide-react'),
      'zustand': path.resolve(__dirname, './node_modules/zustand'),
      'react': path.resolve(__dirname, './node_modules/react'),
      'react-dom': path.resolve(__dirname, './node_modules/react-dom'),
      'clsx': path.resolve(__dirname, './node_modules/clsx'),
      'tailwind-merge': path.resolve(__dirname, './node_modules/tailwind-merge'),
      '@tauri-apps/api': path.resolve(__dirname, './node_modules/@tauri-apps/api'),
    },
    // Ensure dependencies are resolved from frontend's node_modules for shared packages
    preserveSymlinks: false,
    dedupe: ['react', 'react-dom', 'lucide-react', 'zustand', 'clsx', 'tailwind-merge', '@tauri-apps/api'],
  },
  clearScreen: false,
  server: {
    port: 1420,
    strictPort: true,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
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
  optimizeDeps: {
    // Ensure dependencies from shared packages are pre-bundled
    include: ['lucide-react', 'react', 'react-dom', 'zustand', 'clsx', 'tailwind-merge', '@tauri-apps/api'],
  },
  build: {
    target: process.env.TAURI_PLATFORM == 'windows' ? 'chrome105' : 'safari13',
    minify: !process.env.TAURI_DEBUG ? 'esbuild' : false,
    sourcemap: !!process.env.TAURI_DEBUG,
    // Disable code splitting for Android to avoid circular dependency issues
    // All code will be in a single bundle
    rollupOptions: {
      output: {
        manualChunks: undefined,
      },
    },
    // Optimize chunk size warning threshold (Android tablets)
    chunkSizeWarningLimit: 1000,
  },
});

