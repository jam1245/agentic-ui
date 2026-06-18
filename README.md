# Agent-Driven UI — Implementation Guide & Reference

How to let an AI agent drive **charts, KPI cards, timelines, dashboards, risk matrices,
and Gantt views** in a React front end — not just tables. The LLM is your **internal
Genesis** assistant; **no Google (or any other) API key is ever used.**

**React · internal Genesis LLM · MCP-style data tools** — and a contract that's
transport-agnostic, so it drops into AG-UI / CopilotKit if you adopt them later.

> **The one idea:** the agent does **not** render charts. It produces a **structured UI
> payload** — *here is the data, here is what it means, here is how to show it* — and a
> generic React renderer turns that payload into the right component through a **known
> contract**.
>
> **The other half:** every rendered chart also becomes a **first-class conversational
> artifact**. The same render produces an `ArtifactContext` stored in session state, so the
> chat agent can answer follow-ups — *"why did March dip?"*, *"summarize that for
> leadership"*, *"compare this to SPI"* — about what it showed. See
> [docs/09](docs/09-artifact-aware-context.md).

Run one command and you get a **live page**: a Genesis-powered chat on the left that really
plots, and an "under the hood" panel on the right showing the data being **absorbed into
context** and the exact contract payload behind each chart.

---

## The two contracts in one picture

```
User question
   │
   ▼
Genesis agent ──calls──► MCP / data tool ──► structured data (rows)
   │                                              │
   │  ◄────────────────────────────────────────────┘
   ▼
Agent decides the best visualization (intent-driven)
   │
   ├─► AgentUIPayload ──► validate (zod) ──► registry ──► <AgentUIRenderer> ──► chart/table/…
   │      (CONTRACT 1)                                     └─ fallback to table on bad payload
   │
   └─► ArtifactContext ──► session artifact registry
          (CONTRACT 2)            │
                    compact digest fed to future prompts  ← chat stays data-aware
                    full rows rehydrated only on demand     ← get_artifact / dataRef
```

**Contract 1** (`AgentUIPayload`) displays rich UI. **Contract 2** (`ArtifactContext`)
keeps the chat agent aware of what it displayed, so follow-ups keep working.

## Answering the core question

> *When an agent retrieves data, what should it send to the front end?*

**A combination — but structured into one contract:** raw `data` **+** a `component`
choice **+** a `fields` mapping (which keys are the axes) **+** `metadata` (source,
intent, explanation). Not raw data alone (the UI can't decide), and not a rendered chart
(couples the agent to the UI). See [`docs/02-payload-contract.md`](docs/02-payload-contract.md).

| Responsibility | Owner |
| --- | --- |
| What data means, which view fits, field mapping, intent | **Agent (Genesis)** |
| Pixels, theming, axes, interactivity, accessibility, fallback | **React UI** |
| The vocabulary of allowed components + their schemas | **Shared contract** |

The agent picks *from a menu the UI defines*. The UI stays generic; the agent drives it.

---

## Quick start (no key needed to start)

```bash
python3 -m pip install -r agent/requirements.txt   # Windows: python -m pip ...
npm install

# 1. Prove the whole pipeline in a terminal, offline (mock LLM):
python3 scripts/genesis_demo.py --mock

# 2. The live page — chat + charts + context panel (offline mock backend):
npm run dev:genesis          # → http://localhost:5173/
#    click "Show CPI trend…", then "Why did March dip?" and watch the Context panel.

# 3. Go live with the real Genesis LLM:
#    copy .env.example → .env and set LLM_API_KEY + LLM_MODEL (loaded automatically)
#    macOS/Linux: cp .env.example .env   |   Windows: copy .env.example .env
npm run dev:genesis
```

Runs the same on **Windows / macOS / Linux** (Node 18+ and Python 3.10+; keys via `.env`,
no `export`/`set`). Full walkthrough: [docs/10-genesis-internal-llm.md](docs/10-genesis-internal-llm.md)
and [TESTING.md](TESTING.md).

**Contract-only (no LLM at all):** `npm run dev` serves the page; the Gallery tab renders
every component from static payloads. `npm test` runs the contract + artifact tests.

---

## Learn it step by step

A guided path for a developer new to this. **Do step 0 first** — seeing it run makes the
rest concrete — then read the docs in order (each ends with a "Next →" link, so you can
just keep clicking through `docs/`).

| Step | Read / do | What you'll learn |
| --- | --- | --- |
| **0. See it work** | [TESTING.md](TESTING.md) → `npm run dev:genesis` | the whole loop in the browser; click the chips, watch the Context panel |
| **1. The big idea** | [docs/01-architecture.md](docs/01-architecture.md) | why the agent emits a *payload*, not a chart; who owns what |
| **2. Contract 1** | [docs/02-payload-contract.md](docs/02-payload-contract.md) | the `AgentUIPayload` schema, field by field, and why |
| **3. Rendering** | [docs/03-react-rendering.md](docs/03-react-rendering.md) | the registry + one generic `<AgentUIRenderer>` |
| **4. Frontend wiring** | [docs/04-frontend-integration.md](docs/04-frontend-integration.md) | how a payload reaches React (and the optional CopilotKit/AG-UI path) |
| **5. Backend** | [docs/05-backend-and-data-tools.md](docs/05-backend-and-data-tools.md) | data tools / MCP + the hybrid agent loop |
| **6. Examples** | [docs/06-examples.md](docs/06-examples.md) | the same contract across 8 program-management scenarios |
| **7. Roadmap** | [docs/07-implementation-roadmap.md](docs/07-implementation-roadmap.md) | crawl/walk/run rollout + anti-patterns |
| **8. Trust & fallbacks** | [docs/08-validation-and-fallbacks.md](docs/08-validation-and-fallbacks.md) | validate both sides; degrade to a table, never crash |
| **9. Contract 2** | [docs/09-artifact-aware-context.md](docs/09-artifact-aware-context.md) | how charts stay in chat context for follow-ups |
| **10. Run on Genesis** | [docs/10-genesis-internal-llm.md](docs/10-genesis-internal-llm.md) | the internal LLM end to end + a per-prompt demo walkthrough |
| **11. Extend** | [docs/11-add-a-visualization.md](docs/11-add-a-visualization.md) | add your own chart type — a copy-pasteable, 6-step worked example |

New to the codebase and want the fastest "aha"? Read **1 → 2 → 3**, then open the
**Payload** and **Context** tabs while you click chips in the running app. Docs 1 and 10
include rendered diagrams (architecture flow, a turn sequence) to anchor the mental model.

---

## Repository layout

```
docs/                      ← the implementation guide
  01-architecture.md       conceptual architecture & responsibilities
  02-payload-contract.md   CONTRACT 1 schema, field-by-field, with rationale
  03-react-rendering.md    registry + generic renderer pattern
  04-frontend-integration.md   wiring payloads into React (and optional CopilotKit/AG-UI)
  05-backend-and-data-tools.md  data tools / MCP + the Genesis agent loop
  06-examples.md           program-management worked examples
  07-implementation-roadmap.md   crawl/walk/run rollout
  08-validation-and-fallbacks.md  trust boundaries & graceful degradation
  09-artifact-aware-context.md   CONTRACT 2: charts as conversational artifacts
  10-genesis-internal-llm.md     the Genesis backend, end to end (start here to run it)

src/                       ← React reference implementation
  contract/                types.ts + schema.ts (CONTRACT 1) · artifact.ts (CONTRACT 2)
  components/              AgentUIRenderer + registry + renderers/*
  store/artifactRegistry.ts  client artifact registry (digests + rehydration)
  genesis/                 useGenesisChat — live chat state for the landing page
  examples/payloads.ts    canonical example payloads (used by gallery + tests)
  App.tsx                 the landing page: live chat + context/payload/gallery panel

server/genesis_app.py      ← FastAPI backend: drives the UI with the internal Genesis LLM
agent/                     ← Python (Genesis-only; no Google ADK, no Google key)
  genesis_client.py        internal Genesis Completions-API client (+ offline mock)
  genesis_agent.py         hybrid loop: deterministic router + LLM prose → payloads + artifacts
  data_tools.py            MCP/data-layer tools (return rows + source/filters)
  payloads.py              pydantic mirror of CONTRACT 1
  artifacts.py             pydantic mirror of CONTRACT 2 + session-state registry
scripts/genesis_demo.py    ← zero-to-working CLI proof (offline with --mock)
```

---

## Why this repo (vs. the Chainlit prototype it replaces)

The original [`jam1245/agentic-ui`](https://github.com/jam1245/agentic-ui) proved the
*concept* in Chainlit: an agent triggering rich UI via tool calls. This rewrite extracts
that pattern and makes it **production-shaped**, with an explicit, validated contract, an
allow-listed component registry, graceful fallbacks, artifact-aware follow-ups, and your
internal **Genesis** LLM as the backend. The architectural lesson carried over:

**Don't ask the agent to render charts. Ask it to emit structured UI instructions + data
that React renders through a known contract.**
