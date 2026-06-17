# 4. CopilotKit / AG-UI Integration

This is the wiring that carries an `AgentUIPayload` from the ADK agent to a React
component. The contract never changes; only the transport does.

## The mental model

```
Frontend registers available UI tools/components   (useAgentUI → render_ui action)
        ▼
Agent chooses the right component                  (ADK instruction + render_ui tool)
        ▼
Agent calls it with structured props               (the AgentUIPayload)
        ▼
AG-UI carries the tool call as an event            (agent ⇄ frontend protocol)
        ▼
CopilotKit renders the registered React component   (generative UI)
```

AG-UI is the **event protocol** between agent and frontend; CopilotKit is the **React
layer** that subscribes to those events and renders. Google ADK is the **agent runtime**
that emits the tool call.

## Pattern A — one `render_ui` action (recommended)

The whole payload is the argument. The front end validates and dispatches through the
registry, so **adding a chart type needs zero changes here**.

[`src/copilotkit/useAgentUI.tsx`](../src/copilotkit/useAgentUI.tsx):

```tsx
import { useCopilotAction } from "@copilotkit/react-core";
import { AgentUIRenderer } from "../components/AgentUIRenderer";
import { SUPPORTED_COMPONENTS } from "../components/registry";
import { validatePayload } from "../contract";

export function useAgentUI() {
  useCopilotAction({
    name: "render_ui",
    description: `Render a rich UI component instead of a text table. ` +
      `Allowed: ${SUPPORTED_COMPONENTS.join(", ")}.`,
    parameters: [
      { name: "component", type: "string", required: true },
      { name: "title", type: "string", required: true },
      { name: "data", type: "object[]", required: true },
      { name: "fields", type: "object", required: false },
      { name: "metadata", type: "object", required: true },
    ],
    render: ({ args }) => <AgentUIRenderer raw={validatePayload(args).payload} />,
  });
}
```

Mount the app and call the hook:

```tsx
import { CopilotKit } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import { useAgentUI } from "./copilotkit/useAgentUI";

function Chat() {
  useAgentUI();                 // registers render_ui
  return <CopilotChat />;
}

export function Root() {
  return (
    <CopilotKit runtimeUrl="/api/copilotkit" agent="program_analyst">
      <Chat />
    </CopilotKit>
  );
}
```

## Pattern B — one action per component

More explicit; more to maintain. Register N actions, each with typed parameters:

```tsx
useCopilotAction({
  name: "line_chart",
  description: "Render a line chart for a trend over time.",
  parameters: [
    { name: "title", type: "string", required: true },
    { name: "data", type: "object[]", required: true },
    { name: "x", type: "string", required: true },
    { name: "y", type: "string", required: true },
  ],
  render: ({ args }) => (
    <AgentUIRenderer raw={{ component: "line_chart", title: args.title,
      data: args.data, fields: { x: args.x, y: args.y },
      metadata: { source: "agent" } }} />
  ),
});
```

Use Pattern B once the catalog is stable and you want per-component validation surfaced to
the model. You can mix: Pattern A for the long tail, Pattern B for a few high-value ones.

## Connecting Google ADK over AG-UI (self-hosted runtime — no Copilot Cloud)

This is the **fully open-source path**: the self-hosted `@copilotkit/runtime` (MIT, free)
plus the ADK agent exposed over AG-UI. Copilot Cloud is *not* required — it's only a
managed-hosting option. Three processes:

```
React chat ──/api/copilotkit──► CopilotKit runtime ──HttpAgent──► ADK (AG-UI endpoint)
  Vite :5173                       Express :4000                    uvicorn :8000
```

### 1. Expose the ADK agent over AG-UI ([`agent/serve.py`](../agent/serve.py))

```python
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
from fastapi import FastAPI
from .agent import root_agent

adk_agent = ADKAgent(adk_agent=root_agent, app_name="program_analyst_app",
                     user_id="demo_user", use_in_memory_services=True)
app = FastAPI()
add_adk_fastapi_endpoint(app, adk_agent, path="/")   # → http://localhost:8000/
```

`pip install ag_ui_adk fastapi uvicorn` · run `uvicorn agent.serve:app --port 8000`.

### 2. Self-hosted runtime ([`server/copilotkit-runtime.ts`](../server/copilotkit-runtime.ts))

```ts
import { CopilotRuntime, ExperimentalEmptyAdapter, copilotRuntimeNodeHttpEndpoint } from "@copilotkit/runtime";
import { HttpAgent } from "@ag-ui/client";
import express from "express";

const runtime = new CopilotRuntime({
  agents: { program_analyst: new HttpAgent({ url: "http://localhost:8000/" }) },
});
const handler = copilotRuntimeNodeHttpEndpoint({
  endpoint: "/api/copilotkit", runtime,
  serviceAdapter: new ExperimentalEmptyAdapter(),   // LLM lives in ADK, not here
});
express().use("/api/copilotkit", (req, res) => handler(req, res)).listen(4000);
```

The `ExperimentalEmptyAdapter` means **no LLM key in the runtime** — the key stays in the
ADK process. The agent key `program_analyst` must match the `<CopilotKit agent="...">`
prop and the ADK agent's name.

### 3. The chart round trip

```
ADK render_ui(payload, …)  → AG-UI tool-call event → runtime → browser
   → useCopilotAction("render_ui").render(args)   [src/chat/useAdkRenderUI.tsx]
   → <AgentUIRenderer> draws the chart
```

`render_ui` runs **server-side** in ADK (validates + stores the artifact in session
state); CopilotKit surfaces the tool call to the browser where the matching action draws
it. Note the ADK arg shape is nested (`args.payload`), which is why the chat uses
[`useAdkRenderUI`](../src/chat/useAdkRenderUI.tsx) rather than the flat-param `useAgentUI`.

Because both sides validate the **same contract** (pydantic in `render_ui`, zod in
`AgentUIRenderer`), a malformed payload is caught server-side (agent self-corrects) and,
as a backstop, client-side (falls back to a table). See
[08-validation-and-fallbacks.md](08-validation-and-fallbacks.md). Run it all with
`npm run dev:full` — see [TESTING.md](../TESTING.md) Tier 4.

## Interactive round trips

For drill-down, register `render_ui_interactive` with `renderAndWaitForResponse`
([`InteractiveAgentUI.tsx`](../src/copilotkit/InteractiveAgentUI.tsx)). The component
calls `respond({ selected: row })`; AG-UI carries that result back into the agent run, and
the agent renders a follow-up payload. This is the same contract used in both directions.

## Shared state (optional)

CopilotKit also supports shared agent/UI state (e.g. the current program, active filters).
Keep **render payloads** (one-shot, ephemeral visualizations) separate from **shared
state** (durable selections that affect future tool calls). Mixing them makes both harder
to reason about.

Next: [the Google ADK side →](05-google-adk-tools.md)
