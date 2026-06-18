# Agent-Driven UI — Implementation Guide & Reference

How to let an AI agent drive **charts, KPI cards, timelines, dashboards, risk matrices,
and Gantt views** in a React front end — not just tables — on a stack of:

**React · [AG-UI](https://docs.ag-ui.com/introduction) · [CopilotKit](https://docs.copilotkit.ai) · [Google ADK](https://google.github.io/adk-docs/) · MCP tools**

> **The one idea:** the agent does **not** render charts. The agent produces a
> **structured UI payload** — *here is the data, here is what it means, here is how to
> show it* — and a generic React renderer turns that payload into the right component
> through a **known contract**.
>
> **And the other half:** every rendered chart also becomes a **first-class
> conversational artifact**. The same render produces an `ArtifactContext` stored in
> session state, so the chat agent can answer follow-ups — *"why did March dip?"*,
> *"summarize that for leadership"*, *"compare this to SPI"* — about what it showed.
> See [docs/09](docs/09-artifact-aware-context.md).

This repo is both the **developer guide** (`docs/`) and a **runnable reference
implementation** (`src/` React + `agent/` Google ADK) you can hand to the team.

---

## The two contracts in one picture

```
User question
   │
   ▼
ADK Agent ──calls──► MCP / data tool ──► structured data (rows)
   │                                          │
   │  ◄───────────────────────────────────────┘
   ▼
Agent decides the best visualization (intent-driven)
   │
   ▼
render_ui(payload, question, summary)
   │
   ├─► AgentUIPayload ──► AG-UI ──► CopilotKit ──► <AgentUIRenderer>
   │      (CONTRACT 1)                  │  validate (zod) → registry → chart/table/…
   │                                    └─ fallback to table on bad payload
   │
   └─► ArtifactContext ──► session artifact registry (ADK state + client mirror)
          (CONTRACT 2)            │
                    compact digest in every future prompt  ← chat stays data-aware
                    full data rehydrated only on demand     ← get_artifact_data / dataRef
```

**Contract 1** (`AgentUIPayload`) displays rich UI. **Contract 2** (`ArtifactContext`)
keeps the chat agent aware of what it displayed, so follow-ups keep working.

## Answering the team's core question

> *When an agent retrieves data, what should it send to the front end?*

**A combination — but structured into one contract:** raw `data` **+** a `component`
choice **+** a `fields` mapping (which keys are the axes) **+** `metadata` (source,
intent, explanation). Not raw data alone (the UI can't decide), and not a rendered chart
(couples the agent to the UI). See [`docs/02-payload-contract.md`](docs/02-payload-contract.md).

> *How much rendering responsibility belongs to the agent vs. the UI?*

| Responsibility | Owner |
| --- | --- |
| What data means, which view fits, field mapping, intent | **Agent** |
| Pixels, theming, axes, interactivity, accessibility, fallback | **React UI** |
| The vocabulary of allowed components + their schemas | **Shared contract** |

The agent picks *from a menu the UI defines*. The UI stays generic; the agent drives it.

---

## Repository layout

```
docs/                      ← the implementation guide (start here)
  01-architecture.md       conceptual architecture & responsibilities
  02-payload-contract.md   the schema, field-by-field, with rationale
  03-react-rendering.md     registry + generic renderer pattern
  04-copilotkit-agui-integration.md   wiring agent output to React
  05-google-adk-tools.md   data tools vs UI tool; teaching the agent
  06-examples.md           7 program-management worked examples
  07-implementation-roadmap.md   crawl/walk/run rollout
  08-validation-and-fallbacks.md  trust boundaries & graceful degradation
  09-artifact-aware-context.md   CONTRACT 2: charts as conversational artifacts
  10-genesis-internal-llm.md   driving the demos with the internal Genesis LLM

src/                       ← React reference implementation
  contract/                types.ts + schema.ts (CONTRACT 1) · artifact.ts (CONTRACT 2)
  components/              AgentUIRenderer + registry + renderers/*
  copilotkit/             useAgentUI() (render+store) · useArtifactAwareness() (recall)
  chat/                   Tier-4 live chat: ChatApp + useAdkRenderUI (ADK-shaped binding)
  store/artifactRegistry.ts  session artifact registry (digests + rehydration)
  examples/payloads.ts    canonical example payloads (used by demo + tests)
  App.tsx                 standalone demo of all components + artifact digest panel

src/genesis/             ← internal-LLM chat (Genesis) — plain-fetch chat + AgentUIRenderer

server/                    ← backends
  genesis_app.py          FastAPI: drives the demos with the internal Genesis LLM
  copilotkit-runtime.ts   self-hosted CopilotKit runtime (Tier 4), HttpAgent → ADK over AG-UI

agent/                     ← Python: two LLM backends, one set of contracts
  genesis_client.py       internal Genesis Assistants-API client (+ offline mock)
  genesis_agent.py        agent loop over Genesis → validated payloads + artifacts
  data_tools.py           MCP/data-layer tools (return rows + source/filters)
  ui_tools.py             render_ui (renders + stores artifact) · list/get_artifact_data
  payloads.py             pydantic mirror of CONTRACT 1
  artifacts.py            pydantic mirror of CONTRACT 2 + session-state registry
  agent.py / serve.py     Google ADK agent + its AG-UI endpoint (alternative backend)

scripts/genesis_demo.py    ← zero-to-working CLI proof (runs offline with --mock)
```

**Try it locally — start here:** [TESTING.md](TESTING.md). The fastest "this is the goal,
working" path uses your internal **Genesis** LLM and needs **no key to start** (offline
mock), then flips live with a key.

---

## Quick start

### The goal, working — internal Genesis LLM (no key to start)

```bash
python3 -m pip install -r agent/requirements.txt
npm install

# 1. Prove the whole pipeline in a terminal, offline:
python3 scripts/genesis_demo.py --mock

# 2. In the browser (offline mock backend):
npm run dev:genesis        # → http://localhost:5173/genesis.html
#    try: "Show CPI trend for the last six months"  then  "Why did March dip?"

# 3. Go live with the real Genesis LLM:
#    copy .env.example → .env, set LLM_API_KEY + PM_ASSISTANT_ID (loaded automatically)
npm run dev:genesis
```

Runs the same on Windows/macOS/Linux (Node + Python; keys via `.env`, no `export`/`set`
needed). Same contracts and the same `<AgentUIRenderer>` drive every backend — see
[docs/10-genesis-internal-llm.md](docs/10-genesis-internal-llm.md).

### Contract-only demo (no LLM at all)

```bash
npm run dev          # tabs for every example payload + the artifact digest panel
npm test             # contract validation + artifact tests
```

### Alternative backend — Google ADK + self-hosted CopilotKit

```bash
pip install -r agent/requirements.txt
adk web                       # Gemini/Vertex; or wire the full browser loop:
npm run dev:full              # ADK → CopilotKit runtime → React (/chat.html)
```

See [`docs/04-copilotkit-agui-integration.md`](docs/04-copilotkit-agui-integration.md).

---

## Why this repo (vs. the Chainlit prototype it replaces)

The original [`jam1245/agentic-ui`](https://github.com/jam1245/agentic-ui) proved the
*concept* in Chainlit: an agent triggering rich UI via tool calls. This rewrite extracts
that pattern and makes it **production-shaped for your exact stack**, with an explicit,
validated contract, an allow-listed component registry, graceful fallbacks, and a
matching Google ADK agent. The architectural lesson carried over:

**Don't ask the agent to render charts. Ask it to emit structured UI instructions + data
that React renders through a known contract.**
