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

src/                       ← React reference implementation
  contract/                types.ts + schema.ts (CONTRACT 1) · artifact.ts (CONTRACT 2)
  components/              AgentUIRenderer + registry + renderers/*
  copilotkit/             useAgentUI() (render+store) · useArtifactAwareness() (recall)
  chat/                   Tier-4 live chat: ChatApp + useAdkRenderUI (ADK-shaped binding)
  store/artifactRegistry.ts  session artifact registry (digests + rehydration)
  examples/payloads.ts    canonical example payloads (used by demo + tests)
  App.tsx                 standalone demo of all components + artifact digest panel

server/                    ← self-hosted CopilotKit runtime (Tier 4, no Copilot Cloud)
  copilotkit-runtime.ts   Express + @copilotkit/runtime, HttpAgent → ADK over AG-UI

agent/                     ← Google ADK reference implementation (Python)
  data_tools.py           MCP/data-layer tools (return rows + source/filters)
  ui_tools.py             render_ui (renders + stores artifact) · list/get_artifact_data
  payloads.py             pydantic mirror of CONTRACT 1
  artifacts.py            pydantic mirror of CONTRACT 2 + session-state registry
  agent.py                the agent + instruction (viz choice + follow-up recall)
  serve.py                exposes the agent over AG-UI (ag_ui_adk) for Tier 4
```

**Try it locally:** [TESTING.md](TESTING.md) — Tier 1 (browser demo, no keys) →
Tier 4 (`npm run dev:full`: live ADK agent rendering charts in chat via the self-hosted
runtime).

---

## Quick start

> **Just want to try it?** See [TESTING.md](TESTING.md) — Tier 1 runs in the browser with
> **no API key and no agent** (`npm install && npm run dev`).

**React demo (no agent needed — proves the contract + renderers):**

```bash
npm install
npm run dev          # open the demo: tabs for every example payload
npm test             # contract validation tests (incl. fallback behavior)
npm run export:schema  # emit JSON Schema for the agent's tool definition
```

**Google ADK agent:**

```bash
cd agent
pip install -r requirements.txt
adk web              # or: adk run .   — try "Show CPI trend for the last 6 months"
```

See [`docs/04-copilotkit-agui-integration.md`](docs/04-copilotkit-agui-integration.md)
to connect the two over AG-UI + CopilotKit.

---

## Why this repo (vs. the Chainlit prototype it replaces)

The original [`jam1245/agentic-ui`](https://github.com/jam1245/agentic-ui) proved the
*concept* in Chainlit: an agent triggering rich UI via tool calls. This rewrite extracts
that pattern and makes it **production-shaped for your exact stack**, with an explicit,
validated contract, an allow-listed component registry, graceful fallbacks, and a
matching Google ADK agent. The architectural lesson carried over:

**Don't ask the agent to render charts. Ask it to emit structured UI instructions + data
that React renders through a known contract.**
