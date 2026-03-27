import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'
import { visualizer } from 'rollup-plugin-visualizer'

export default defineConfig({
  plugins: [
    vue(),

    // ── F11.3: PWA ─────────────────────────────────────────
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favico.png', 'icons/*.png'],
      manifest: false, // use public/manifest.json directly
      workbox: {
        // Cache shell assets (JS/CSS/fonts) offline
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        // Route all navigation to index.html (SPA)
        navigateFallback: '/index.html',
        navigateFallbackDenylist: [/^\/api\//],
      },
    }),

    // ── F11.5: Bundle visualizer (generates stats.html on build) ──
    visualizer({
      filename: 'dist/stats.html',
      open: false,
      gzipSize: true,
      brotliSize: true,
    }),
  ],

  server: {
    host: '0.0.0.0',
    port: 5173,
  },

  resolve: {
    alias: {
      '@': '/src',
    },
  },

  build: {
    // ── F11.5: Code splitting ──────────────────────────────
    rollupOptions: {
      output: {
        manualChunks: {
          // Vendor: large, rarely-changing libraries
          'vendor-vue': ['vue', 'vue-router', 'pinia'],
          'vendor-primevue': ['primevue', '@primeuix/themes'],
          'vendor-echarts': ['echarts', 'vue-echarts'],
          'vendor-axios': ['axios'],
        },
      },
    },
    // Warn when a single chunk exceeds 300 KB gzipped (approx 900 KB raw)
    chunkSizeWarningLimit: 900,
  },
})
