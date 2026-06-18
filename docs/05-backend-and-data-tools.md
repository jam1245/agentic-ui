# 5. Backend & Data Tools

The backend has three jobs: **fetch data** (from MCP / enterprise systems), **pick the
visualization and answer questions about it**, and **emit the two contracts** (render
payload + artifact).

**This is a Google ADK backend.** The primary path is an ADK `LlmAgent` brained by the
internal **Genesis** LLM via LiteLLM (no Google Cloud / Gemini / Google key) — it reasons,
calls the data tools, and drives the UI via the `render_chart` tool. See the full framework
in [12-adk-architecture.md](12-adk-architecture.md). A deterministic, LLM-free engine
(`agent/genesis_agent.py`) is the **offline/mock fallback** for demos and CI.

```
DATA tools  = data access / computation   → return rows      (agent/tools/data_tools.py)
ADK agent   = LlmAgent (LiteLlm→Genesis)  → reasons + calls tools  (agent/adk_agents/…)
render_chart= the data→UI tool            → payload + artifact      (agent/tools/render_tools.py)
fallback    = deterministic engine        → offline/mock answers    (agent/genesis_agent.py)
```

## Data tools — your MCP / enterprise layer

[`agent/tools/data_tools.py`](../agent/tools/data_tools.py): plain functions that return
rows plus light source metadata. They know nothing about charts.

```python
def get_cpi_trend(program: str, months: int = 6) -> dict:
    """Return monthly Cost Performance Index for a program."""
    return {
        "rows": [{"month": "Jan", "cpi": 0.92}, ...],
        "source": "EVMS MCP",
        "filters": {"program": program, "months": months},
    }
```

In production these wrap real MCP servers. The `source`/`filters` they return flow straight
into the payload's `metadata` and the artifact's provenance — for free.

## The ADK agent loop (primary)

[`agent/adk_agents/program_analyst/agent.py`](../agent/adk_agents/program_analyst/agent.py)
is an ADK `LlmAgent(model=get_model(), tools=[…])`. ADK's native tool-calling loop (running
on Genesis via LiteLLM) does the reasoning:

- the agent calls a **data tool** to get rows (so it answers with real numbers),
- it calls **`render_chart`** ([render_tools.py](../agent/tools/render_tools.py)) to plot —
  that tool fetches authoritative rows, builds + validates the `AgentUIPayload`, records an
  artifact, and stages both into ADK session state; [runner.py](../agent/runner.py) returns
  them to React,
- it calls **`get_artifact_data` / `list_artifacts`** to answer follow-ups about a chart it
  already showed (plans, director summaries, "what should I worry about").

## The deterministic fallback engine (offline/mock)

[`agent/genesis_agent.py`](../agent/genesis_agent.py) is an LLM-free engine used when
`GENESIS_MOCK=1` or no key is set. It maps a request to a data tool + component
(`route_chart`) and computes answers from the rows (`_analyze`: highest/lowest, average,
difference, trend, top/least risk, worst variance). Always correct and clean, so demos and
CI run with zero credentials and the UI is identical to the ADK path.

We assemble + validate an `AgentUIPayload` (pydantic), store an `ArtifactContext`, and
return both. Questions about a chart rehydrate its rows from the artifact registry and are
answered by `_analyze`. Full walkthrough: [10](10-genesis-internal-llm.md).

## The visualization mapping (deterministic router)

Components map to **intent**, not just data shape (this lives in `route_chart` in
`genesis_agent.py`):

```
Trend over time            → line_chart
Compare discrete categories → bar_chart
Likelihood × impact         → risk_matrix
Headline metrics / health   → kpi_card
Plan vs actual detail        → variance_table
Chronological events        → timeline
Overlapping task durations  → gantt
Cause grouping / RCA        → fishbone
Anything else / raw rows    → table
```

## Validation at the boundary

Every payload is validated with pydantic before it leaves the backend, and again with zod
in the browser. Two layers because the producer is an LLM — see
[08-validation-and-fallbacks.md](08-validation-and-fallbacks.md). The JSON Schema the agent
should target can be exported from the TS contract (`npm run export:schema`) so the agent
and UI never drift.

## Keeping Python and TypeScript aligned

[`agent/payloads.py`](../agent/payloads.py) mirrors `src/contract/types.ts`;
[`agent/artifacts.py`](../agent/artifacts.py) mirrors `src/contract/artifact.ts`. A CI step
can diff `TypeAdapter(AgentUIPayload).json_schema()` against the exported zod schema to
catch drift.

Next: [worked examples →](06-examples.md)
