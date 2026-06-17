# 3. React Rendering Pattern

The front end stays **generic**: it never special-cases a question or a program. It has
(1) a **registry** of renderers, (2) a **validator**, and (3) one **entry component**.

## The registry (the allow-list)

[`src/components/registry.tsx`](../src/components/registry.tsx) is the only place that maps
a `ComponentKind` to a React renderer. If a kind isn't here, the agent can't render it.

```tsx
export const REGISTRY: Record<ComponentKind, Renderer> = {
  table: DataTable,
  line_chart: LineChartView,
  bar_chart: BarChartView,
  kpi_card: KpiCardGrid,
  risk_matrix: RiskMatrix,
  timeline: TimelineView,
  gantt: GanttView,
  variance_table: VarianceTable,
  fishbone: FishboneView,
};

export const SUPPORTED_COMPONENTS = Object.keys(REGISTRY); // advertised to the agent
```

`SUPPORTED_COMPONENTS` is exported and fed to the agent's tool description, so the UI's
capabilities and the agent's options come from **one list**.

## The generic renderer

The classic `switch` works, but a registry scales better and keeps the allow-list in one
place. The conceptual switch the team asked about:

```tsx
function AgentUIRenderer({ payload }) {
  switch (payload.component) {
    case "line_chart": return <LineChart data={payload.data} x={payload.fields.x} y={payload.fields.y} />;
    case "bar_chart":  return <BarChart  data={payload.data} x={payload.fields.x} y={payload.fields.y} />;
    case "risk_matrix":return <RiskMatrix data={payload.data} />;
    case "kpi_card":   return <KPICardGrid data={payload.data} />;
    default:           return <DataTable data={payload.data} />;
  }
}
```

The production version ([`AgentUIRenderer.tsx`](../src/components/AgentUIRenderer.tsx))
adds the two things that matter for trust:

```tsx
export function AgentUIRenderer({ raw }: { raw: unknown }) {
  const { payload, ok, error } = validatePayload(raw);   // 1. validate (never trust the LLM)
  const Renderer = getRenderer(payload);                 // 2. registry lookup (allow-list)
  return (
    <section className="agent-ui" data-component={payload.component}>
      <header><h3>{payload.title}</h3>{!ok && <span>fallback: table</span>}</header>
      <Renderer payload={payload} />
      <footer>
        {payload.metadata.explanation}     {/* why this chart — from the agent */}
        Source: {payload.metadata.source}  {/* provenance — from the data tool */}
      </footer>
    </section>
  );
}
```

Every agent-driven visualization is therefore **self-describing**: title, the chart, and a
footer that says where the data came from and why this view was chosen.

## How renderers stay generic

A renderer reads only `data` + `fields`, never hard-coded keys. That's why one component
serves every domain:

```tsx
// LineChartView — works for CPI, headcount, burn rate… anything with x/y
<Line dataKey={payload.fields.y} />
<XAxis dataKey={payload.fields.x} />
```

So "show CPI by month" and "show defects by week" hit the **same** `LineChartView`; only
the payload differs. Charts use [recharts](https://recharts.org); swap in your own lib
without touching the contract.

## Adding a new visualization (4 steps, one place each)

1. **Type** — add the kind + payload interface in `contract/types.ts`.
2. **Schema** — add the zod variant in `contract/schema.ts`.
3. **Renderer** — add a component in `components/renderers/`.
4. **Register** — one line in `components/registry.tsx`.

The agent picks it up automatically because `SUPPORTED_COMPONENTS` feeds its tool
description (re-export the JSON Schema and redeploy the agent).

## Interactivity / drill-down

Display-only is the common case. When a component must send a result back to the agent
(user clicks a risk → agent fetches its mitigation), use CopilotKit's
`renderAndWaitForResponse` — see
[`src/copilotkit/InteractiveAgentUI.tsx`](../src/copilotkit/InteractiveAgentUI.tsx) and
[04-copilotkit-agui-integration.md](04-copilotkit-agui-integration.md). The user's
selection flows back over AG-UI events and the agent continues the run.

Next: [wiring this to the agent →](04-copilotkit-agui-integration.md)
