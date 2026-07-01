import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Accept the Host header from VS Code dev tunnels / other *.devtunnels.ms URLs
    // (Vite 5 blocks unknown hosts by default). localhost/127.0.0.1 stay allowed.
    allowedHosts: ['.devtunnels.ms'],
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
})
