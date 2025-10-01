import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  root: __dirname,
  plugins: [react()],
  base: './',
  css: {
    postcss: path.resolve(__dirname, 'postcss.config.js'),
  },
  server: {
    port: 3333,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5555',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      // Proxy backend OpenAPI + docs directly so Swagger UI works under Vite dev
      '/openapi.json': {
        target: 'http://127.0.0.1:5555',
        changeOrigin: true,
      },
      '/docs': {
        target: 'http://127.0.0.1:5555',
        changeOrigin: true,
      },
      '/thumbnails': {
        target: 'http://127.0.0.1:5555',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'router': ['react-router-dom'],
          'ui-vendor': ['@radix-ui/react-tabs', '@radix-ui/react-scroll-area', '@radix-ui/react-checkbox'],
          'icons': ['lucide-react'],
          'utils': ['clsx', 'class-variance-authority', 'tailwind-merge']
        }
      }
    },
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    },
    sourcemap: false,
    target: 'es2020',
    chunkSizeWarningLimit: 1000
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
