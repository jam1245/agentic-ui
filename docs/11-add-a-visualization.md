# 11. Extend: Add a New Visualization

A copy-pasteable walkthrough for adding a component the agent can render. We'll add an
**`area_chart`** (like `line_chart`, filled). The pattern is the same for any new view.

There are **two sides** to touch — TypeScript (so React can render + validate it) and
Python (so the agent can choose it). Each side is small and isolated.

```
TypeScript:  types → schema → renderer → registry        (UI can render it)
Python:      payloads → router/intent                     (agent can choose it)
```

---

## TypeScript side (the UI can render it)

### 1. Add the type — `src/contract/types.ts`

Add the kind to the union, define the payload, and add it to `AgentUIPayload`:

```ts
export type ComponentKind =
  | "table" | "line_chart" | "bar_chart" | "kpi_card" | "risk_matrix"
  | "timeline" | "gantt" | "variance_table" | "fishbone"
  | "area_chart";                                   // ← add

export interface AreaChartPayload extends BasePayload {  // ← add
  component: "area_chart";
  fields: FieldMapping & { x: string; y: string };
}

export type AgentUIPayload =
  | TablePayload | LineChartPayload | BarChartPayload | KpiCardPayload
  | RiskMatrixPayload | TimelinePayload | GanttPayload | VarianceTablePayload
  | FishbonePayload
  | AreaChartPayload;                               // ← add
```

### 2. Add the zod variant — `src/contract/schema.ts`

Add a branch to the discriminated union so payloads are validated (and bad ones fall back
to a table):

```ts
z.object({
  ...base,
  component: z.literal("area_chart"),
  fields: fields.required({ x: true, y: true }),
}),
```

### 3. Write the renderer — `src/components/renderers/AreaChartView.tsx`

Read only `data` + `fields` so it stays generic (works for any dataset):

```tsx
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { AreaChartPayload } from "../../contract";

export function AreaChartView({ payload }: { payload: AreaChartPayload }) {
  const { data, fields } = payload;
  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={data} margin={{ top: 16, right: 24, bottom: 8, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey={fields.x} />
        <YAxis />
        <Tooltip />
        <Area type="monotone" dataKey={fields.y} stroke="#2563eb" fill="#bfdbfe" />
      </AreaChart>
    </ResponsiveContainer>
  );
}
```

### 4. Register it — `src/components/registry.tsx`

Import it and add **one line**. This is the allow-list; `SUPPORTED_COMPONENTS` updates
automatically:

```ts
import { AreaChartView } from "./renderers/AreaChartView";

export const REGISTRY: Record<ComponentKind, Renderer> = {
  // …existing…
  area_chart: AreaChartView,                        // ← add
};
```

**The UI can now render `area_chart`.** Add an example to
[`src/examples/payloads.ts`](../src/examples/payloads.ts) and it shows up in the Gallery
tab; `npm test` will assert it validates.

---

## Python side (the agent can choose it)

### 5. Mirror the type — `agent/payloads.py`

```python
class AreaChartPayload(_Base):
    component: Literal["area_chart"] = "area_chart"
    fields: FieldMapping

AgentUIPayload = Union[
    # …existing…
    AreaChartPayload,
]
```

### 6. Teach the router — `agent/genesis_agent.py`

Add an intent so a user question maps to the new component (deterministic = reliable):

```python
if "cumulative" in q or "area" in q:
    return ChartIntent(
        "get_cpi_trend", {"program": "P-117", "months": 6}, "area_chart",
        "Cumulative CPI", "trend_analysis", {"x": "month", "y": "cpi"},
        "Filled area emphasizes the trend's magnitude over time.",
    )
```

(If you also add a new *data* tool, register it in `TOOLS` and `agent/data_tools.py`.)

---

## Verify

```bash
npm run typecheck        # the discriminated union forces you to handle the new kind
npm test                 # contract + fallback tests
npm run dev:genesis      # ask "show cumulative CPI as an area chart"
```

## Checklist

- [ ] `types.ts` — kind in `ComponentKind`, payload interface, added to `AgentUIPayload`
- [ ] `schema.ts` — zod variant in the discriminated union
- [ ] `renderers/XxxView.tsx` — reads only `data` + `fields`
- [ ] `registry.tsx` — one line
- [ ] `payloads.py` — pydantic mirror + union
- [ ] `genesis_agent.py` — a `route_chart` intent (and a data tool if needed)
- [ ] `npm run typecheck && npm test` green

## Why it's this small

The contract is a **discriminated union** and the registry is the **single allow-list**, so
a new visualization is additive and isolated — no transport, no agent-loop, and no other
renderer changes. That's the payoff of the two-contract design ([01](01-architecture.md),
[02](02-payload-contract.md)).

← back to the [README](../README.md) · the guide starts at [01-architecture.md](01-architecture.md)
