# Agent-Driven UI — Implementation Guide & Reference

How to let an AI agent drive **charts, KPI cards, timelines, dashboards, risk matrices,
and Gantt views** in a React front end — not just tables.

This is a **Google ADK** project. The agents use the ADK framework (orchestration,
tool-calling, plug-and-play sub-agents), but the **LLM is the internal Genesis model via
LiteLLM** — **no Google Cloud, no Gemini, no Google API key.** ADK is the framework;
Genesis is the brain. See [docs/12-adk-architecture.md](docs/12-adk-architecture.md).

**React · Google ADK · internal Genesis LLM (LiteLLM) · MCP-style data tools**

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

# 3. Go live with the real ADK + Genesis agent:
#    copy .env.example → .env and set LLM_API_KEY (+ LLM_MODEL, LLM_API_BASE)
#    macOS/Linux: cp .env.example .env   |   Windows: copy .env.example .env
npm run dev:genesis            # /api/health now reports mode:"adk"
```

With a key, requests run through the **Google ADK agent** (Genesis LLM via LiteLLM); with no
key they run the deterministic offline engine — same UI either way. Runs the same on
**Windows / macOS / Linux** (Node 18+, Python 3.10+). See
[docs/12-adk-architecture.md](docs/12-adk-architecture.md) and [TESTING.md](TESTING.md).

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
| **5. Backend** | [docs/05-backend-and-data-tools.md](docs/05-backend-and-data-tools.md) | data tools / MCP + the agent loop |
| **6. Examples** | [docs/06-examples.md](docs/06-examples.md) | the same contract across 8 program-management scenarios |
| **7. Roadmap** | [docs/07-implementation-roadmap.md](docs/07-implementation-roadmap.md) | crawl/walk/run rollout + anti-patterns |
| **8. Trust & fallbacks** | [docs/08-validation-and-fallbacks.md](docs/08-validation-and-fallbacks.md) | validate both sides; degrade to a table, never crash |
| **9. Contract 2** | [docs/09-artifact-aware-context.md](docs/09-artifact-aware-context.md) | how charts stay in chat context for follow-ups |
| **10. Run on Genesis** | [docs/10-genesis-internal-llm.md](docs/10-genesis-internal-llm.md) | the Genesis LLM + the offline/mock engine |
| **11. Extend** | [docs/11-add-a-visualization.md](docs/11-add-a-visualization.md) | add your own chart type — a copy-pasteable, 6-step worked example |
| **12. ADK framework** | [docs/12-adk-architecture.md](docs/12-adk-architecture.md) | how Google ADK + LiteLlm→Genesis powers the agents (foundational) |

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
  10-genesis-internal-llm.md     the Genesis LLM + the offline/mock engine
  11-add-a-visualization.md      extend: add a chart type
  12-adk-architecture.md         the Google ADK framework (LiteLlm→Genesis) — foundational

src/                       ← React reference implementation (UNCHANGED by the ADK move)
  contract/                types.ts + schema.ts (CONTRACT 1) · artifact.ts (CONTRACT 2)
  components/              AgentUIRenderer + registry + renderers/*
  genesis/                 useGenesisChat — live chat state for the landing page
  examples/payloads.ts    canonical example payloads (used by gallery + tests)
  App.tsx                 the landing page: live chat + context/payload/gallery panel

server/genesis_app.py      ← FastAPI: runs the ADK agent (real) or deterministic engine (mock)
agent/                     ← Google ADK project (ADK framework + Genesis LLM via LiteLLM)
  config/model_config.py   get_model() → LiteLlm("openai/gpt-oss-120b", Genesis base)
  adk_agents/
    orchestrator/agent.py  root_agent — routes to specialists (ADK sub_agents delegation)
    cam_agent/ risk_agent/ pm_agent/ rcca_agent/   domain specialists (each consults a Genesis assistant)
    program_analyst/       single general agent (alternative to the orchestrator)
    _factory.py            make_specialist(...) — plug-and-play sub-agent builder
  tools/data_tools.py      data tools (rows + source/filters)
  tools/render_tools.py    render_chart / render_structured — the data→UI bridge
  tools/artifact_tools.py  list/get_artifact_data (data-aware follow-ups)
  tools/external_assistant_tool.py   Genesis Assistants bridge (call_*_assistant_v2)
  runner.py                ADK Runner: run a turn, extract staged payloads/artifacts
  payloads.py / artifacts.py   pydantic mirrors of the two contracts
  genesis_agent.py         deterministic offline engine (mock/CI fallback, no LLM)
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
