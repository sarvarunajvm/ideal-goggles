import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { codecovVitePlugin } from '@codecov/vite-plugin'

const isAnalyze = process.env.ANALYZE === 'true'

export default defineConfig(async () => ({
  root: __dirname,
  plugins: [
    react(),
    // Generate bundle analysis report (only when ANALYZE=true)
    ...(isAnalyze
      ? [
          (await import('rollup-plugin-visualizer')).visualizer({
            filename: './dist/stats.html',
            open: false,
            gzipSize: true,
            brotliSize: true,
            template: 'treemap'
          }) as any
        ]
      : []),
    // Codecov bundle analysis (enabled in CI when token is available)
    codecovVitePlugin({
      enableBundleAnalysis: process.env.CODECOV_TOKEN !== undefined,
      bundleName: 'ideal-goggles-frontend',
      uploadToken: process.env.CODECOV_TOKEN,
      uploadOverrides: {
        // Ensure proper branch/commit detection in CI
        branch: process.env.GITHUB_HEAD_REF || process.env.GITHUB_REF_NAME,
        sha: process.env.GITHUB_SHA,
        slug: process.env.GITHUB_REPOSITORY,
      },
    }),
  ],
  base: './',
  css: {
    postcss: path.resolve(__dirname, 'postcss.config.js'),
  },
  server: {
    host: '127.0.0.1',
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
}))
