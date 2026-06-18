# 7. Implementation Roadmap

A practical crawl/walk/run path. Don't build all nine components on day one — prove the
*contract* with three, then scale by adding renderers.

## Phase 0 — Decide the contract (½ day)

- Adopt `AgentUIPayload` ([02-payload-contract.md](02-payload-contract.md)) as-is or trim
  it. **One** schema, owned in one file, mirrored in pydantic.
- Decide transport: start simple (one HTTP `/api/chat` that returns the payload).
- Set up the schema-export → JSON-Schema step and a CI drift check (pydantic vs zod).

## Phase 1 — Crawl: three components (1 sprint)

Ship the smallest set that proves the loop end to end:

1. **table** — you already have this; it becomes the fallback.
2. **line_chart** — the canonical "trend" answer.
3. **kpi_card** — the canonical "summary" answer.

Deliverables:
- `validatePayload` wired into `<AgentUIRenderer>` with **table fallback** on any failure.
- Backend payload validation (pydantic) before returning to the UI.
- Router/agent teaching: trend→line_chart, summary→kpi_card, else→table.
- Tests: every example payload validates; malformed payloads fall back to a table.

**Exit criteria:** ask "show CPI trend" and "summarize program health" → correct chart,
correct source/explanation footer, and a garbage payload degrades to a table without
crashing.

## Phase 2 — Walk: comparison + status (1 sprint)

Add `bar_chart` and `risk_matrix`. These exercise:
- categorical x-axis (bar) and 2-D placement (matrix),
- intent disambiguation (the agent must pick line vs bar vs matrix correctly).

Invest here in the **agent instruction + a small eval set** of question→expected-component
pairs. Visualization-choice quality is now the bottleneck, not rendering.

## Phase 3 — Run: schedule, detail, RCA (1–2 sprints)

Add `timeline`, `gantt`, `variance_table`, `fishbone` as demand warrants. Each is the same
4-step add (type → schema → renderer → registry line). Consider:
- **drill-down** via `renderAndWaitForResponse` for risk matrix / variance table,
- **shared state** for the active program/filters.

## Phase 4 — Harden

- CI drift check between zod and pydantic schemas.
- Telemetry: log `{question, component, userIntent, ok}` to measure how often the agent
  picks the right view and how often payloads fall back.
- A11y + theming pass on renderers (the contract doesn't change).
- Rate/size limits on `data` (cap rows; the agent should aggregate, not dump 10k rows).

## What to add later (backlog)

- variance **waterfall**, drill-down **detail tables**, **document evidence cards**,
  geospatial, gauge/bullet KPIs.
- Each is additive and isolated — that's the whole benefit of the contract.

## Anti-patterns to avoid

- ❌ Letting the agent emit React/SVG/HTML. Keep it to structured payloads.
- ❌ A new data tool per question ("show_cpi_chart"). Data tools fetch *data*; the agent
  picks the component and composes them.
- ❌ Reshaping `data` into recharts-specific structures in the agent. Keep `data` neutral;
  renderers adapt.
- ❌ Skipping validation "because the model is usually right." The boundary is an LLM;
  validate on both sides.

Next: [validation & fallbacks →](08-validation-and-fallbacks.md)
