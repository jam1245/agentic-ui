# 5. Google ADK Pattern

ADK tools are structured functions an agent calls with defined inputs and outputs. We use
**two kinds** of tools, and the separation is the core of the architecture:

```
DATA tool  = data access / computation     → returns rows      (data_tools.py)
UI   tool  = visualization instruction     → returns a payload (ui_tools.py)
AGENT      = the reasoning bridge between them                  (agent.py)
```

The agent already knows how to call a data tool and get rows. The new capability is: after
getting rows, **decide how to show them and call `render_ui`**.

## Data tools — unchanged from today

[`agent/data_tools.py`](../agent/data_tools.py). Plain functions that wrap MCP/enterprise
systems and return rows + light source metadata. They know nothing about charts.

```python
def get_cpi_trend(program: str, months: int = 6) -> dict:
    """Return monthly Cost Performance Index for a program."""
    ...
    return {
        "rows": [{"month": "Jan", "cpi": 0.92}, ...],
        "source": "EVMS MCP",
        "filters": {"program": program, "months": months},
    }
```

> In production these call MCP servers. ADK has first-class MCP support, so each MCP tool
> can be registered directly; the wrappers here just make the example runnable and give you
> a place to normalize/source-tag results.

## The UI tool — the contract boundary

[`agent/ui_tools.py`](../agent/ui_tools.py). **One** tool, `render_ui`, whose argument is a
full `AgentUIPayload`. It validates against the pydantic models and echoes the payload; ADK
returns it to the front end.

```python
from pydantic import TypeAdapter
from .payloads import AgentUIPayload

_adapter = TypeAdapter(AgentUIPayload)

def render_ui(payload: dict) -> dict:
    """Render a rich UI component for the user. Call this instead of a text table."""
    validated = _adapter.validate_python(payload)   # raises → agent self-corrects
    return {"rendered": True, "payload": validated.model_dump(exclude_none=True)}
```

Validation at this boundary is what makes the agent **self-correcting**: a bad payload
raises, ADK feeds the error back to the model, and it retries within the same turn —
server-side graceful fallback before the payload ever reaches the browser.

## The agent — teaching visualization choice

[`agent/agent.py`](../agent/agent.py). The instruction is the highest-leverage prompt in
the system. Tie each component to **intent**, not to data shape alone:

```
Trend over time            → line_chart
Compare discrete categories → bar_chart
Likelihood × impact         → risk_matrix
Headline metrics / health   → kpi_card
Chronological events        → timeline
Overlapping task durations  → gantt
Plan vs actual detail        → variance_table
Cause grouping / RCA        → fishbone
Anything else / raw rows    → table
```

```python
root_agent = Agent(
    name="program_analyst",
    model="gemini-2.0-flash",
    instruction=INSTRUCTION,                       # the rules above
    tools=[
        data_tools.get_cpi_trend,
        data_tools.get_spi_by_control_account,
        data_tools.get_top_risks,
        data_tools.get_program_health,
        data_tools.get_cam_variance,
        render_ui,                                  # the UI tool
    ],
)
```

## End-to-end flow for one question

```
User: "Show CPI trend for the last six months."
  → agent calls get_cpi_trend(program="P-117", months=6)
  → tool returns rows + source "EVMS MCP"
  → agent reasons: trend over time → line_chart, x=month, y=cpi
  → agent calls render_ui({component:"line_chart", data:rows, fields:{x,y}, metadata})
  → render_ui validates → returns payload
  → AG-UI event → CopilotKit → <AgentUIRenderer> → <LineChartView>
  → agent's text reply: one sentence of insight (no data dump)
```

## Giving the agent the exact schema

So the model emits valid payloads, hand it the JSON Schema generated from the contract:

```bash
npm run export:schema   # → dist/agent-ui-payload.schema.json
```

Use it as `render_ui`'s argument schema (ADK accepts pydantic models / JSON Schema for
tool args). One source → both the TS UI and the agent's tool definition.

## Keeping pydantic and zod aligned

[`agent/payloads.py`](../agent/payloads.py) mirrors `src/contract/types.ts`. Add a CI step
that diffs `TypeAdapter(AgentUIPayload).json_schema()` against the exported zod schema so
the two never drift.

Next: [worked examples →](06-examples.md)
