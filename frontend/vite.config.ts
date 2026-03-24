import { defineConfig, type UserConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { codecovVitePlugin } from '@codecov/vite-plugin'

const isAnalyze = process.env.ANALYZE === 'true'

export default defineConfig(async (_env): Promise<UserConfig> => {
  return {
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
        rewrite: (path: string) => path.replace(/^\/api/, ''),
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
        manualChunks(id: string) {
          if (id.includes('node_modules/react-dom') || id.includes('node_modules/react/')) {
            return 'react-vendor'
          }
          if (id.includes('node_modules/react-router-dom')) {
            return 'router'
          }
          if (id.includes('node_modules/@radix-ui')) {
            return 'ui-vendor'
          }
          if (id.includes('node_modules/lucide-react')) {
            return 'icons'
          }
          if (id.includes('node_modules/clsx') || id.includes('node_modules/class-variance-authority') || id.includes('node_modules/tailwind-merge')) {
            return 'utils'
          }
        }
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
  }
})
