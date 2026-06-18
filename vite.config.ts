import { resolve } from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      input: {
        // Tier 1 — key-free demo
        main: resolve(__dirname, "index.html"),
        // Tier 4 — live agent chat (ADK + CopilotKit)
        chat: resolve(__dirname, "chat.html"),
        // Genesis — internal LLM chat
        genesis: resolve(__dirname, "genesis.html"),
      },
    },
  },
  server: {
    proxy: {
      // Tier 4 — CopilotKit self-hosted runtime
      "/api/copilotkit": process.env.RUNTIME_URL ?? "http://localhost:4000",
      // Genesis backend (server/genesis_app.py)
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
