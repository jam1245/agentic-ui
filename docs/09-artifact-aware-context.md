# 9. Artifact-Aware Conversation Context

> Rendering a chart is not enough. The chart must become a **first-class conversational
> artifact**. The user should be able to keep interacting with the chart, table, timeline,
> or dashboard after it is rendered.

The system needs **two** contracts:

1. **Agent-to-UI rendering contract** (`AgentUIPayload`) — lets the system *display* rich
   UI. Covered in [02](02-payload-contract.md).
2. **Artifact-to-agent context contract** (`ArtifactContext`) — lets the main chat agent
   *stay data-aware* and reason about what was displayed in future turns. **This page.**

## The problem with a one-way render

Today's flow ends at the pixels:

```
question → agent → tool → data → render chart   ✗ dead end
```

So when the user then asks "why did March dip?", "summarize this for leadership",
"compare this to SPI", or "turn that into action items", the agent has no idea what "this"
/ "that" refers to, or what data backed the chart. The chart is a dead-end UI object.

## The fix: every render also produces an artifact

```
question → agent → tool → data → AgentUIPayload ──► render (React)
                                       │
                                       └─normalize─► ArtifactContext ──► session artifact registry
                                                                              │
                                          compact digest in every future prompt
                                                                              │
                                          full data rehydrated only on demand
```

One render, two outputs, **one shared `artifactId`** linking them.

## The two payloads side by side

```ts
// 1. UI Rendering Payload — how to draw it (sent to React)
type AgentUIPayload = {
  artifactId?: string;          // links to the stored context
  component: "line_chart" | "table" | "kpi_card" | "risk_matrix" | ...;
  title: string;
  data: Record<string, unknown>[];
  fields: { x?: string; y?: string; groupBy?: string; value?: string };
  metadata: { source: string; explanation?: string; filtersApplied?: ... };
};

// 2. Artifact Context — what it means (kept by the chat agent)
type ArtifactContext = {
  artifactId: string;
  artifactType: "chart" | "table" | "kpi_card" | "risk_matrix" | ...;
  title: string;
  originalUserQuestion: string;   // anchors "this"/"that"
  sourceTool: string;             // e.g. evms_mcp.get_cpi_history
  sourceSystem?: string;
  dataRef?: string;               // pointer to rehydrate full data
  dataSample?: Record<string, unknown>[];   // a few rows
  fullData?: Record<string, unknown>[];     // stored, NOT prompted
  fields: Record<string, string>;
  filtersApplied?: Record<string, unknown>;
  assumptions?: string[];
  agentInterpretation: string;
  summaryForFutureTurns: string;  // THIS goes in the prompt
  createdAt: string;
};
```

Source of truth: [`src/contract/artifact.ts`](../src/contract/artifact.ts) and
[`agent/artifacts.py`](../agent/artifacts.py). `toArtifactContext()` derives one from the
other so they can't drift.

## The key design question: what do we actually store?

| Option | Verdict |
| --- | --- |
| **1. Full dataset in LLM context every turn** | ❌ Blows the prompt budget; fails on enterprise-scale data; slow and costly. |
| **2. Compact summary + schema + filters + data reference** | ✅ Cheap, scales, auditable. The agent reasons from the summary and re-queries when it needs rows. |
| **3. Sample + pointer to rehydrate later** | ✅ Best blend: a few rows give the agent shape awareness; the pointer fetches the rest on demand. |

**Recommended (what this repo implements): a blend of 2 and 3.**

```
Store:  summary + schema(fields) + filters + dataSample(≤5 rows) + dataRef
Prompt: ONLY the digest (summary + schema + filters + sample + ids)
Fetch:  fullData on demand via get_artifact_data(artifactId)  ← or re-query via dataRef
```

This is enforced by the **digest** projection
([`toDigest`](../src/contract/artifact.ts)): the full dataset lives in the registry but is
*never* part of what the chat agent sees each turn. The
[artifact test](../src/contract/artifact.test.ts) asserts exactly this (`fullData` absent
from the digest; rows recoverable on demand).

> Rule of thumb: **summary in the prompt, data on demand.** If you find yourself pasting
> hundreds of rows into context, store a `dataRef` instead and rehydrate.

## Implementation per stack layer

### MCP / tools — data **plus** light semantic metadata

Tools return raw rows **and** source/filter tags (not full chart specs). The semantic
*interpretation* is the agent's job, but provenance should ride along with the data:

```python
# agent/data_tools.py
return {"rows": [...], "source": "EVMS MCP", "filters": {"program": "P-117", "months": 6}}
```

This gives the artifact its `sourceTool`, `sourceSystem`, and `filtersApplied` for free.

### Genesis agent — create + store the artifact each turn

[`agent/genesis_agent.py`](../agent/genesis_agent.py). When the agent renders, it normalizes
the payload into an `ArtifactContext` and stores it in **session state**:

```python
artifact = to_artifact_context(
    payload,
    original_user_question=user_question,
    source_tool=source_tool,
    summary_for_future_turns=summary,
)
payload.artifactId = artifact.artifactId
store_artifact(session.state, artifact)        # ← per-conversation session state
```

The loop also handles recall directly:
- prior artifact **digests** are injected into every prompt (resolve "this"/"that"),
- a `{"action":"get_artifact","artifactId":...}` step rehydrates full rows on demand, and
- the turn reports `context_used` so the UI can show a "🧠 used context" badge.

Session state is the **backend source of truth** and persists across turns (the Genesis
thread keeps the conversation; the artifact registry keeps the data).

### Transport — `artifactId` ties render to context

The rendered payload carries its `artifactId`, so the frontend correlates the on-screen
component with its stored context without a second channel. Over the HTTP transport the
server simply returns `{ payloads, artifacts, context_used }`; over AG-UI/CopilotKit the
same fields ride events and `useCopilotReadable` — the contract is unchanged.

### Frontend — where artifact context lives

```
┌── backend session store (server/genesis_app.py; swap for a DB) ← source of truth
│        ▲ the agent reasons from this across turns
│        │
└── client registry (src/store/artifactRegistry.ts)             ← drives the Context panel
```

**Recommendation: both.** The backend store is authoritative (the agent reasons from it);
the client store ([`src/store/artifactRegistry.ts`](../src/store/artifactRegistry.ts), a
dependency-free `useSyncExternalStore` registry — swap in Zustand/Redux if you have one)
mirrors it for the UI. For the single-process demo the in-memory backend store is enough;
for production, persist server-side so context survives restarts / scales across pods.

## Recommended flow

```
1. Data tool / MCP returns structured rows (+ source + filters).
2. The Genesis agent interprets the result and picks a visualization.
3. Agent emits a UI rendering payload (AgentUIPayload).
4. Same payload is normalized into ArtifactContext (shared artifactId).
5. ArtifactContext is stored in the session artifact registry.
6. Future prompts get a COMPACT digest (summary + schema + sample) — never the full rows.
7. Full data is rehydrated only when a follow-up needs it (get_artifact / dataRef re-query).
```

## Free-form questions about plotted data (and the canvas direction)

A rendered chart isn't just answerable by canned follow-ups — the chat reasons over the
chart's **actual rows**. `run_turn` ([`agent/genesis_agent.py`](../agent/genesis_agent.py))
routes each message:

- **a chart request** ("show CPI trend") → plot it + store the artifact;
- **a question about plotted data** ("explain the difference between Jan and Jun CPI",
  "which control account is worst?", "why did March dip?") → **do not re-plot**. Pick the
  relevant artifact (by topic), and answer from its full rows.

**How the answer is produced (important):** data-awareness does **not** depend on the LLM
parsing rows correctly — a reasoning model on a text endpoint proved unreliable (it leaked
reasoning/symbols). Instead the answer is **computed in Python from the artifact's rows**
(`_analyze` in [`agent/genesis_agent.py`](../agent/genesis_agent.py)) — highest/lowest,
average, difference between two points, specific-value lookup, trend, worst risk, worst
variance, etc. That computed fact is always correct and clean. The LLM is then asked only
to **reword the correct fact**, and its output is accepted through a **strict filter**
(rejecting markup, reasoning, odd symbols); if it fails, the computed sentence is shown.

By default the **computed sentence is the answer** — it's already clean and professional, so
there's no dependence on the model behaving. LLM rewording is **opt-in**
(`GENESIS_REPHRASE=1`) because a reasoning model on the raw endpoint tends to leak
scaffolding ("the answer should be: we have…"); when enabled, it only rewords a correct
fact and must pass the strict filter, else the computed sentence is shown. Set
`GENESIS_DEBUG=1` to print the raw model output and see exactly what it returned.

> **Toward a multi-plot canvas:** this is exactly the mechanism that scales to a canvas of
> many triggered plots. Every plot pushes its `ArtifactContext` (rows + digest) into the
> session registry; the chat is handed the canvas inventory each turn and rehydrates the
> rows it needs. To grow further: (1) select the relevant artifact by embedding/keyword
> when there are many, (2) pass *multiple* artifacts' rows for cross-chart questions
> ("compare CPI to SPI"), and (3) cap rows / summarize large series before they enter the
> prompt. The contract already carries everything needed; these are retrieval refinements,
> not architecture changes.

## Worked follow-up examples

### Example 1 — CPI trend, then "why did March dip?"

User: *"Show CPI trend for the last six months."* → line chart rendered; stored:

```json
{
  "artifactId": "artifact_cpi_trend_001",
  "artifactType": "line_chart",
  "title": "CPI Trend — Last 6 Months",
  "originalUserQuestion": "Show CPI trend for the last six months.",
  "sourceTool": "evms_mcp.get_cpi_history",
  "fields": { "x": "month", "y": "cpi" },
  "filtersApplied": { "dateRange": "last_6_months" },
  "agentInterpretation": "The user requested trend analysis, so a line chart was selected.",
  "summaryForFutureTurns": "CPI improved from 0.92 to 0.98 over six months, with a dip in March."
}
```

User: *"Why did March dip?"*
→ The digest tells the agent this refers to `artifact_cpi_trend_001`. The summary already
flags the March dip; for the *cause*, the agent calls `get_artifact_data` (or re-queries
`evms_mcp.get_cpi_history` via `dataRef` for March-level detail) and explains — no need to
re-ask the user what "March" refers to.

### Example 2 — Risk matrix, then "which should I brief leadership on?"

User: *"Show top risks by likelihood and impact."* → risk matrix stored with
`fields: {x:"likelihood", y:"impact", label:"risk"}` and `summaryForFutureTurns: "4 risks;
Supplier delay (4×5) is the top exposure."`

User: *"Which of these should I brief leadership on?"*
→ The agent reads the stored matrix context, `get_artifact_data` if needed, sorts by
likelihood×impact, and recommends *Supplier delay* and *Staffing gap* — using the SAME
data it rendered, not a fresh guess.

### Example 3 — KPI cards, then "turn that into an executive summary"

User: *"Summarize program health."* → KPI cards stored with each metric + status.

User: *"Turn that into an executive summary."*
→ "that" resolves to the KPI artifact via the digest. The agent composes prose from the
stored values (CPI 0.94 ⚠, SPI 1.02 ✓, 12 open risks ⚠, EAC −$1.2M ✗) — and can render a
follow-up artifact (e.g. a `table` briefing or a new chart) that *also* gets stored.

## Key principle for developers

You need **both** contracts:

- the **agent-to-UI rendering contract** so the system can *display* rich UI, and
- the **artifact-to-agent context contract** so the main chat stays *data-aware* and can
  reason about what it displayed in future turns.

Build the first and you get charts. Build both and you get a conversation that keeps
working *with* those charts.

Next: [run it all on the internal Genesis LLM →](10-genesis-internal-llm.md)
