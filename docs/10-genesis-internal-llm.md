# 10. Using the Internal Genesis LLM (zero → working)

This is the **default LLM backend for the demos**. Genesis is an OpenAI *Assistants*-style
API (`/threads` → `/messages` → `/runs` → poll → read), reached at
`https://api.ai.us.lmco.com/v1` with a bearer `LLM_API_KEY` and an `assistant_id`. It does
not change the contracts: Genesis drives the **same** `AgentUIPayload` + `ArtifactContext`,
rendered by the **same** `<AgentUIRenderer>` as every other tier.

> Key idea: Genesis returns *text*, not native tool calls. So we give it a tiny JSON
> "action" protocol and run a reasoning loop over it. The model picks the data tool and the
> visualization; **our code supplies the real numbers** (from the data tools) so the model
> never fabricates data.

## Zero → working in one command (no key needed)

Every example runs offline with a built-in mock client, so a developer can see the whole
pipeline before they have credentials:

```bash
# CLI: the full canonical conversation, printing validated payloads + artifacts
python3 scripts/genesis_demo.py --mock

# In the browser:
python3 -m pip install -r agent/requirements.txt
npm install
npm run dev:genesis      # starts the Genesis backend (mock) + Vite
# open http://localhost:5173/  → chat on the left, context/payload/gallery on the right
```

`/api/health` returns `{"mode":"mock"}` until you add a key.

## Switch to the real Genesis LLM

Copy `.env.example` to `.env` and fill in your values — that's it. Both the Python backend
(`python-dotenv`) and Vite load `.env` automatically, so there's **no `export` (mac/Linux)
or `set`/`$env:` (Windows)** to remember:

```dotenv
LLM_API_KEY=your-internal-key
PM_ASSISTANT_ID=your-program-mgmt-assistant-id
# GENESIS_BASE_URL defaults to https://api.ai.us.lmco.com/v1
```

```bash
# macOS/Linux: cp .env.example .env   |   Windows: copy .env.example .env
python3 scripts/genesis_demo.py   # real LLM (use `python` on Windows), same output shape
npm run dev:genesis               # browser, now reports mode:"genesis"
```

The server auto-detects: if `LLM_API_KEY` + `PM_ASSISTANT_ID` are present (and
`GENESIS_MOCK` is unset) it uses the real client; otherwise the mock.

## How it works

```
Browser (App.tsx, "/") ──POST /api/chat──► server/genesis_app.py
                                               │
                                       agent/genesis_agent.run_turn()
                                               │
              ┌────────────────────────────────┼─────────────────────────────┐
              ▼                                 ▼                              ▼
   GenesisClient.ask(prompt)         data_tools.* (real rows)        artifacts registry
   (threads/runs/poll)              attached to the payload          (session state)
              │                                 │                              │
              └──────► validated AgentUIPayload + ArtifactContext ◄────────────┘
                                               │
                              JSON back to the browser → <AgentUIRenderer>
```

Files:
- [`agent/genesis_client.py`](../agent/genesis_client.py) — reusable Assistants-API client
  (**reuses one thread per conversation** for memory) + `MockGenesisClient` for offline.
- [`agent/genesis_agent.py`](../agent/genesis_agent.py) — the action-protocol loop. Produces
  validated payloads, stores artifacts, handles drill-down (`get_artifact`).
- [`server/genesis_app.py`](../server/genesis_app.py) — FastAPI: `POST /api/chat`,
  `GET /api/artifacts`, `GET /api/health`. In-memory per-session client + registry.
- [`src/genesis/useGenesisChat.ts`](../src/genesis/useGenesisChat.ts) + [`src/App.tsx`](../src/App.tsx)
  — the landing page's plain-fetch chat that renders returned payloads with `<AgentUIRenderer>`
  and shows the context/payload panels.
- [`scripts/genesis_demo.py`](../scripts/genesis_demo.py) — CLI proof (`--mock` or real).

### The action protocol the assistant follows

The assistant replies with exactly one JSON object per turn:

```jsonc
// new data question → pick a data tool AND the visualization
{"action":"fetch_data","tool":"get_cpi_trend","args":{"program":"P-117","months":6},
 "then":{"component":"line_chart","title":"CPI Trend — Last 6 Months","userIntent":"trend_analysis",
         "fields":{"x":"month","y":"cpi"},"summary":"CPI rose with a dip in March.",
         "explanation":"Line chart for a trend over time."}}

// follow-up needing the prior chart's rows ("why did March dip?")
{"action":"get_artifact","artifactId":"artifact_line_chart_..."}

// follow-up answered from context (no new chart)
{"action":"reply","text":"..."}
```

Parsing is defensive (strips fences / stray prose); anything unparseable degrades to a
plain text reply, and any payload that fails validation degrades to a table
([08](08-validation-and-fallbacks.md)).

## Why this still satisfies both contracts

- **Contract 1 (render):** `fetch_data.then` *is* the visualization spec; we merge it with
  real tool rows and validate with pydantic → a clean `AgentUIPayload`.
- **Contract 2 (artifacts):** every render is normalized to an `ArtifactContext` and stored
  in session state; follow-ups get the compact digests in-prompt and rehydrate full rows
  via `get_artifact`. Exactly the behavior proven in
  [09-artifact-aware-context.md](09-artifact-aware-context.md).

## Transport: now vs. later

Genesis is the only LLM backend here, reached over a simple HTTP transport. If you later
adopt CopilotKit/AG-UI, only the transport changes — the contracts and renderers don't:

| | This repo (HTTP) | If you adopt CopilotKit/AG-UI |
| --- | --- | --- |
| LLM | **internal Genesis Assistants API** | **internal Genesis** (unchanged) |
| Transport | `POST /api/chat` → FastAPI | AG-UI events via self-hosted `@copilotkit/runtime` |
| Frontend glue | `useGenesisChat` + `<AgentUIRenderer>` | `useCopilotAction("render_ui")` + same renderer |
| Contracts / renderers | **identical** | **identical** |

See [04-frontend-integration.md](04-frontend-integration.md) for the optional CopilotKit
wiring. No Google key in either case.

## Production notes

- Sessions are in-memory (keyed by `session_id`). Swap for a real store so threads +
  artifact context survive restarts and scale across instances.
- Keep `LLM_API_KEY` server-side only (it lives in the Python backend, never the browser).
- The mock client is for demos/CI; it is never used when a key is configured.

← back to the [README](../README.md) · see also [TESTING.md](../TESTING.md)
