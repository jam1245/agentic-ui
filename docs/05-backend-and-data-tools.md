# 5. Backend & Data Tools

The backend has three jobs: **fetch data** (from MCP / enterprise systems), **let the LLM
choose a visualization**, and **emit the two contracts** (render payload + artifact). The
LLM is the internal **Genesis** assistant — no Google ADK, no Google key.

```
DATA tools  = data access / computation     → return rows      (agent/data_tools.py)
AGENT loop  = reasoning bridge over Genesis → payload + artifact (agent/genesis_agent.py)
LLM         = internal Genesis Assistants API                   (agent/genesis_client.py)
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

## The agent loop over Genesis

Genesis returns *text*, not native tool calls, so [`agent/genesis_agent.py`](../agent/genesis_agent.py)
gives it a small JSON **action protocol** and runs the reasoning loop. The model picks the
data tool and the presentation; **our code attaches the real rows**, so the model never
fabricates numbers.

```jsonc
// the assistant replies with one action per turn
{"action":"fetch_data","tool":"get_cpi_trend","args":{"program":"P-117","months":6},
 "then":{"component":"line_chart","title":"CPI Trend — Last 6 Months",
         "fields":{"x":"month","y":"cpi"},"summary":"CPI rose, dipped in March.",
         "explanation":"Line chart for a trend over time."}}
```

We run the tool, assemble + validate an `AgentUIPayload` (pydantic), store an
`ArtifactContext`, and return both. Follow-ups use `{"action":"get_artifact",...}` to
rehydrate prior rows, and `{"action":"reply",...}` to answer from context. Full protocol +
the system instruction that teaches visualization choice: [10](10-genesis-internal-llm.md).

## Teaching visualization choice

Map components to **intent**, not just data shape (this lives in `SYSTEM_INSTRUCTION` in
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
