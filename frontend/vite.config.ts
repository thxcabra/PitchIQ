import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The API base is injected at build/runtime via VITE_API_URL (see .env.example).
// In dev we also proxy /api to the backend so the app works with no env set.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: process.env.VITE_API_URL || "http://127.0.0.1:8000",
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ""),
      },
    },
  },
});
