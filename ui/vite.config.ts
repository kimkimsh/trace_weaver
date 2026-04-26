import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwind from "@tailwindcss/vite";
import { TanStackRouterVite } from "@tanstack/router-plugin/vite";
import path from "node:path";

// In dev, the daemon runs on 127.0.0.1:7777. We proxy /api/* and /ws so the
// SPA can use same-origin URLs and the WebSocket upgrade just works.
export default defineConfig({
  plugins: [
    TanStackRouterVite({ target: "react", autoCodeSplitting: true }),
    react(),
    tailwind(),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:7777",
        changeOrigin: false,
        ws: true,
      },
      "/ext": {
        target: "http://127.0.0.1:7777",
        changeOrigin: false,
      },
    },
  },
  build: {
    // The Python wheel bundles ui/dist as src/traceweaver/ui_static. We keep
    // the structure flat so FastAPI can mount it directly.
    outDir: "dist",
    emptyOutDir: true,
    sourcemap: true,
  },
});
