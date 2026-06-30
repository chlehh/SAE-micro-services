import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Plus de passerelle : le frontend appelle chaque service sur son port
// (http://localhost:8001..8005). Le CORS est activé côté services.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
})
