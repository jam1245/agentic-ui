/**
 * Self-hosted CopilotKit Runtime (Tier 4) — the open-source `@copilotkit/runtime`, NOT
 * Copilot Cloud. This is the server-side middle layer between the React frontend and the
 * ADK agent.
 *
 *   React chat  ──/api/copilotkit──►  THIS server  ──HttpAgent──►  ADK (AG-UI @ :8000)
 *
 * It registers the ADK agent (exposed by agent/serve.py over AG-UI) as a remote agent via
 * AG-UI's HttpAgent. The LLM lives inside the ADK agent, so the runtime uses the
 * ExperimentalEmptyAdapter (no LLM key needed here — the key goes to the ADK process).
 *
 * Run: `npm run dev:runtime`  (or all three tiers at once: `npm run dev:full`)
 */
import express from "express";
import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNodeHttpEndpoint,
} from "@copilotkit/runtime";
import { HttpAgent } from "@ag-ui/client";

const ADK_AGENT_URL = process.env.ADK_AGENT_URL ?? "http://localhost:8000/";
const PORT = Number(process.env.RUNTIME_PORT ?? 4000);

// The agent key ("program_analyst") MUST match the `agent` prop in <CopilotKit> and is how
// the runtime routes requests to this remote agent.
const runtime = new CopilotRuntime({
  agents: {
    program_analyst: new HttpAgent({ url: ADK_AGENT_URL }),
  },
});

const app = express();

const handler = copilotRuntimeNodeHttpEndpoint({
  endpoint: "/api/copilotkit",
  runtime,
  // Empty adapter: the model runs in the ADK agent, not in the runtime.
  serviceAdapter: new ExperimentalEmptyAdapter(),
});

app.use("/api/copilotkit", (req, res) => handler(req, res));

app.listen(PORT, () => {
  console.log(`CopilotKit runtime (self-hosted) on http://localhost:${PORT}/api/copilotkit`);
  console.log(`  → forwarding agent "program_analyst" to ADK at ${ADK_AGENT_URL}`);
});
