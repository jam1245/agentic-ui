# 5. Backend & Data Tools

The backend has three jobs: **fetch data** (from MCP / enterprise systems), **pick the
visualization and answer questions about it**, and **emit the two contracts** (render
payload + artifact). The LLM is the internal **Genesis** model — no Google ADK, no Google
key. Crucially, the structure and the answers are **computed deterministically**; the LLM
is optional polish (see below).

```
DATA tools  = data access / computation        → return rows      (agent/data_tools.py)
AGENT loop  = deterministic router + analytics  → payload + artifact + answers (agent/genesis_agent.py)
LLM         = internal Genesis (chat endpoint)  → conversational answers + fallback (agent/genesis_client.py)
```

## Data tools — your MCP / enterprise layer

[`agent/data_tools.py`](../agent/data_tools.py): plain functions that return rows plus
light source metadata. They know nothing about charts.

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

## The hybrid agent loop

`gpt-oss-120b` is a reasoning model that resists clean structured output, so
[`agent/genesis_agent.py`](../agent/genesis_agent.py) does the reliable work in Python and
treats the model as optional:

- **`route_chart(question)`** deterministically maps a chart request to a data tool +
  component + field mapping (structure can't be broken by the model),
- the **data tool** supplies the real rows (the model never fabricates numbers),
- **`_converse(...)`** answers *questions about plotted data* by sending the LLM a rich brief
  (the chart's rows + computed key facts + the canvas inventory) over the **chat endpoint**,
  which returns the model's final answer (not its chain-of-thought). This lets it converse —
  plans, director summaries, "what should I worry about" — not just recite numbers.
- **`_analyze(question, artifact, rows)`** is the deterministic fallback: if the LLM output is
  unusable (or `GENESIS_NO_LLM=1`, or offline/mock), it computes the answer from the rows
  (highest/lowest, average, difference, specific lookup, trend, top/least risk, worst
  variance) — always correct and clean. So the reply is never broken or content-free.

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
