import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // Proxy API calls to FastAPI during development
  server: {
    proxy: {
      '/login':   'http://localhost:8000',
      '/signup':  'http://localhost:8000',
      '/users':   'http://localhost:8000',
      '/ws':      { target: 'ws://localhost:8000', ws: true },
    },
  },
  build: {
    outDir: '../frontend/dist',
    emptyOutDir: true,
  },
})
