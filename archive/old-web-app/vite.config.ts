/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  // For a GitHub Pages *project* site (https://<user>.github.io/<repo>/), the app must be
  // served from a sub-path. The deploy workflow sets VITE_BASE_PATH to "/<repo>/" automatically;
  // locally (npm run dev / a custom domain later) it just falls back to "/".
  base: process.env.VITE_BASE_PATH || '/',
  test: {
    environment: 'node',
  },
})
