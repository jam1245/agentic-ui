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
        // Tier 4 — live agent chat
        chat: resolve(__dirname, "chat.html"),
      },
    },
  },
  server: {
    // Forward the chat's /api/copilotkit calls to the self-hosted runtime (Tier 4).
    proxy: {
      "/api/copilotkit": process.env.RUNTIME_URL ?? "http://localhost:4000",
    },
  },
  test: {
    environment: "node",
    include: ["src/**/*.test.ts"],
  },
});
