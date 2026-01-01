import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3100,
    watch: {
      usePolling: true
    },
    proxy: {
      '/api': {
        // Use backend service name in Docker, fallback to localhost for local dev
        target: process.env.VITE_API_URL || 'http://backend:8100',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})
