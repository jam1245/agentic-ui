# 2. The Payload Contract

The contract is the whole game. Get this right and everything else is plumbing.

Source of truth: [`src/contract/types.ts`](../src/contract/types.ts) (types),
[`src/contract/schema.ts`](../src/contract/schema.ts) (runtime validation), and the
Python mirror [`agent/payloads.py`](../agent/payloads.py).

## The shape

```ts
type AgentUIPayload = {
  component: "table" | "line_chart" | "bar_chart" | "kpi_card"
           | "risk_matrix" | "timeline" | "gantt" | "variance_table" | "fishbone";
  title: string;
  userIntent?: "trend_analysis" | "comparison" | "distribution" | "status_summary"
             | "schedule" | "root_cause" | "detail_lookup" | "ranking" | "composition";
  data: Record<string, unknown>[];          // the rows — straight from the data tool
  fields?: {                                 // which keys map to which roles
    x?: string; y?: string; groupBy?: string; value?: string; label?: string;
  };
  metadata: {
    source: string;                          // which MCP/tool produced this
    explanation?: string;                    // why this component (shown to the user)
    filtersApplied?: Record<string, unknown>;
    retrievedAt?: string;
  };
};
```

## Why these five parts (the design rationale)

This directly answers *"should the agent return raw data, a chart recommendation, a viz
spec, UI instructions, or metadata?"* — **the contract bundles the useful subset of all of
them**, and deliberately omits the dangerous ones.

| Part | What it is | Why it's in the contract |
| --- | --- | --- |
| `component` | a **recommendation**, constrained to an allow-list | The agent's intent in one enum. Not free-form ("render however") because the UI can only draw what it has a renderer for. |
| `data` | **raw rows** | The UI needs the actual numbers. Passed through unchanged from the data tool — the agent should not reshape into chart-library-specific structures. |
| `fields` | **semantic mapping** | The bridge between generic data and a generic renderer. `{x: "month", y: "cpi"}` is what lets one `<LineChart>` draw *any* dataset. This is the "viz spec" — but minimal and declarative, not imperative drawing code. |
| `userIntent` | **meaning** | Lets the UI add intent-appropriate affordances and lets you evaluate/route. |
| `metadata` | **provenance + reasoning** | `source` answers "where did this come from"; `explanation` answers "why this chart" — both travel with the data so the UI is self-describing and auditable. |

### What is deliberately NOT in the contract

- **No rendering code / SVG / React.** That would couple the agent to the UI and is a
  security and maintainability hazard. The agent recommends; React renders.
- **No pixel/layout details** (colors, widths, fonts). Those belong to the design system,
  not the agent. The agent owns *what and why*, not *how it looks*.
- **No chart-library-specific shapes.** `data` stays neutral rows; each renderer adapts.

## Component-specific requirements

Most components share the base shape; some require extra fields (enforced by zod):

| Component | Requires | Notes |
| --- | --- | --- |
| `line_chart` | `fields.x`, `fields.y` | optional `referenceLine` (e.g. CPI target 1.0) |
| `bar_chart` | `fields.x`, `fields.y` | optional `orientation` |
| `kpi_card` | each row has `label`, `value` | optional `status` ∈ good/warning/critical/neutral |
| `risk_matrix` | `fields.x` (likelihood), `fields.y` (impact) | optional `scale`, `fields.label` |
| `timeline` | each row has `date`, `title` | — |
| `gantt` | each row has `task`, `start`, `end` | optional `percentComplete`, `status` |
| `variance_table` | `fields.label`, `columns[]` | columns flagged `kind:"variance"` get ▲▼ coloring |
| `fishbone` | `problem`, rows have `category`, `cause` | grouped into bones by category |
| `table` | — | the universal fallback; optional `columns` for ordering |

## Keeping Python, TypeScript, and the LLM in sync

Three representations of one contract — they must not drift:

```
contract/schema.ts (zod)  ──npm run export:schema──►  dist/agent-ui-payload.schema.json
        │                                                        │
        │ infers                                                 │ reference schema for
        ▼                                                        ▼ the agent / LLM
contract/types.ts (TS)                              agent/payloads.py (pydantic)
        │                                                        │
   React renderers                                   backend payload validation
```

Recommended CI check: export the zod JSON Schema and diff it against
`TypeAdapter(AgentUIPayload).json_schema()` from pydantic; fail the build on drift.

## A complete example

```json
{
  "component": "line_chart",
  "title": "CPI Trend — Last 6 Months",
  "userIntent": "trend_analysis",
  "data": [
    { "month": "Jan", "cpi": 0.92 },
    { "month": "Feb", "cpi": 0.95 },
    { "month": "Mar", "cpi": 0.98 }
  ],
  "fields": { "x": "month", "y": "cpi" },
  "referenceLine": { "value": 1.0, "label": "Target" },
  "metadata": {
    "source": "EVMS MCP",
    "explanation": "Line chart selected because the user asked for a trend over time.",
    "filtersApplied": { "program": "P-117", "months": 6 }
  }
}
```

More worked examples: [06-examples.md](06-examples.md).

Next: [the React rendering pattern →](03-react-rendering.md)
