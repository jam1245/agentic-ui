import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    // Proxy the chat API to the Genesis backend (server/genesis_app.py).
    proxy: {
      "/api/chat": process.env.GENESIS_URL ?? "http://localhost:8800",
      "/api/artifacts": process.env.GENESIS_URL ?? "http://localhost:8800",
      "/api/health": process.env.GENESIS_URL ?? "http://localhost:8800",
    },
  },
  test: {
    environment: "node",
    include: ["src/**/*.test.ts"],
  },
});
