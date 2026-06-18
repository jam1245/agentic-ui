# 4. Frontend Integration

How an `AgentUIPayload` gets from the agent to a rendered React component. The contract is
**transport-agnostic** — it does not care how the payload arrives. This project ships the
simplest transport (HTTP/JSON to a FastAPI backend); the same payload drops into AG-UI /
CopilotKit unchanged if you adopt them later.

## The transport this repo uses (HTTP/JSON)

```
Browser (App.tsx) ──POST /api/chat──► server/genesis_app.py ──► Genesis agent loop
        ▲                                                              │
        └──────────────── { text, payloads[], artifacts[], context_used[] } ◄┘
```

- [`src/genesis/useGenesisChat.ts`](../src/genesis/useGenesisChat.ts) holds the chat state
  and calls `/api/chat`.
- Each returned payload is handed to [`<AgentUIRenderer>`](../src/components/AgentUIRenderer.tsx),
  which validates it (zod) and dispatches through the registry — falling back to a table on
  any bad payload ([08](08-validation-and-fallbacks.md)).
- `artifacts[]` (compact digests) drive the **Context** panel; `context_used[]` drives the
  "🧠 used context" badge that proves a follow-up reused stored data ([09](09-artifact-aware-context.md)).

That's the whole integration: **POST a message, render the returned payloads.** No
component-specific frontend code — adding a chart type is a renderer + a schema entry, not
new transport.

## The registry is the allow-list

[`src/components/registry.tsx`](../src/components/registry.tsx) maps each `ComponentKind`
to a renderer and is the single list of components the agent may choose from. The Genesis
agent is told exactly this set; it cannot invent one. To add a visualization: add the type
([02](02-payload-contract.md)) → zod variant → renderer → one registry line.

## Optional: CopilotKit / AG-UI (if that's your stack)

This contract was designed to be carried by [AG-UI](https://docs.ag-ui.com) events and
rendered by [CopilotKit](https://docs.copilotkit.ai) generative UI, a natural fit if you
standardize on them. The shape is unchanged — you'd register one CopilotKit action whose
argument **is** the `AgentUIPayload`:

```tsx
useCopilotAction({
  name: "render_ui",
  description: `Render a rich UI component. Allowed: ${SUPPORTED_COMPONENTS.join(", ")}.`,
  parameters: [
    { name: "component", type: "string", required: true },
    { name: "title", type: "string", required: true },
    { name: "data", type: "object[]", required: true },
    { name: "fields", type: "object", required: false },
    { name: "metadata", type: "object", required: true },
  ],
  render: ({ args }) => <AgentUIRenderer raw={args} />,
});
```

To use that path you need a CopilotKit runtime pointed at an AG-UI-compatible agent. Genesis
is an Assistants-style HTTP API, so you'd put a thin AG-UI adapter in front of the Genesis
agent loop (`agent/genesis_agent.py`) and register it with the self-hosted, open-source
`@copilotkit/runtime` (no Copilot Cloud needed). It is not wired in this repo — the HTTP
transport above is simpler and fully working — but the **contract, renderers, registry, and
artifact behavior are identical**, so the migration is transport-only.

Next: [the backend & data tools →](05-backend-and-data-tools.md)
