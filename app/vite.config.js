import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [react()],

  // Vite root is the frontend folder — index.html lives there
  root: path.join(__dirname, 'frontend'),

  // Build output: app/dist/ (loaded by Electron in production)
  build: {
    outDir: path.join(__dirname, 'dist'),
    emptyOutDir: true,
  },

  server: {
    port: 5173,
    strictPort: true,  // Fail if port is already in use
    open: false,       // Never open a browser tab — Electron is the UI
  },

  // Use relative paths for assets so Electron can load them
  base: './',
});
