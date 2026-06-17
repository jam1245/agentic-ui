# 6. Worked Examples

Realistic program-management scenarios. Each shows the **user question**, the
**`AgentUIPayload` the agent emits**, and **what renders**. All of these are live in
[`src/examples/payloads.ts`](../src/examples/payloads.ts) — run `npm run dev` to see them,
and they're asserted valid by [the contract test](../src/contract/schema.test.ts).

---

## A — CPI Trend (line chart)

> **User:** "Show CPI trend for the last six months."
> **Agent reasoning:** trend over time → `line_chart`, x=month, y=cpi, target line at 1.0.

```json
{
  "component": "line_chart",
  "title": "CPI Trend — Last 6 Months",
  "userIntent": "trend_analysis",
  "data": [{ "month": "Jan", "cpi": 0.92 }, { "month": "Feb", "cpi": 0.95 }, { "month": "Mar", "cpi": 0.98 }],
  "fields": { "x": "month", "y": "cpi" },
  "referenceLine": { "value": 1.0, "label": "Target" },
  "metadata": { "source": "EVMS MCP", "explanation": "Line chart selected because the user asked for a trend over time." }
}
```

→ `<LineChartView>` with a dashed target line. Agent text: *"CPI improved from 0.92 to
1.01 and is now at target."*

---

## B — SPI by Control Account (bar chart)

> **User:** "Compare SPI across control accounts."
> **Agent reasoning:** comparison of discrete categories → `bar_chart`.

```json
{
  "component": "bar_chart",
  "title": "SPI by Control Account",
  "userIntent": "comparison",
  "data": [{ "account": "CA-100", "spi": 1.04 }, { "account": "CA-200", "spi": 0.91 }, { "account": "CA-400", "spi": 0.86 }],
  "fields": { "x": "account", "y": "spi" },
  "metadata": { "source": "EVMS MCP", "explanation": "Bar chart selected to compare SPI across discrete control accounts." }
}
```

→ `<BarChartView>`. Agent text: *"CA-400 is the schedule laggard at 0.86."*

---

## C — Top Risks (risk matrix)

> **User:** "Show top program risks by likelihood and impact."

```json
{
  "component": "risk_matrix",
  "title": "Top Program Risks",
  "userIntent": "distribution",
  "data": [
    { "risk": "Supplier delay", "likelihood": 4, "impact": 5 },
    { "risk": "Staffing gap", "likelihood": 3, "impact": 4 }
  ],
  "fields": { "x": "likelihood", "y": "impact", "label": "risk" },
  "scale": { "likelihoodMax": 5, "impactMax": 5 },
  "metadata": { "source": "Risk Register MCP", "explanation": "Risk matrix selected to position risks by likelihood × impact." }
}
```

→ `<RiskMatrix>` 5×5, risks placed in red/yellow/green cells by score.

---

## D — Program Health (KPI cards)

> **User:** "Summarize program health."

```json
{
  "component": "kpi_card",
  "title": "Program Health Summary",
  "userIntent": "status_summary",
  "data": [
    { "label": "CPI", "value": 0.94, "status": "warning" },
    { "label": "SPI", "value": 1.02, "status": "good" },
    { "label": "Open Risks", "value": 12, "status": "warning" },
    { "label": "EAC Variance", "value": "-$1.2M", "status": "critical" }
  ],
  "metadata": { "source": "EVMS MCP", "explanation": "KPI cards selected for a headline health summary." }
}
```

→ `<KpiCardGrid>`, color-coded by status.

---

## E — Milestones (timeline)

> **User:** "What milestones are coming up?"

```json
{
  "component": "timeline",
  "title": "Upcoming Milestones",
  "userIntent": "schedule",
  "data": [
    { "date": "2026-07-15", "title": "PDR", "description": "Preliminary Design Review", "status": "good" },
    { "date": "2026-09-01", "title": "CDR", "description": "Critical Design Review" },
    { "date": "2026-11-30", "title": "TRR", "description": "Test Readiness Review", "status": "warning" }
  ],
  "metadata": { "source": "IMS MCP", "explanation": "Timeline selected for chronological milestone review." }
}
```

→ `<TimelineView>`.

---

## F — Integration & Test Schedule (Gantt)

> **User:** "Show the integration and test schedule."

```json
{
  "component": "gantt",
  "title": "Integration & Test Schedule",
  "userIntent": "schedule",
  "data": [
    { "task": "Subsystem integration", "start": "2026-07-01", "end": "2026-08-15", "percentComplete": 60, "status": "good" },
    { "task": "Environmental test", "start": "2026-08-10", "end": "2026-09-20", "percentComplete": 10, "status": "warning" }
  ],
  "metadata": { "source": "IMS MCP", "explanation": "Gantt selected to show overlapping task durations." }
}
```

→ `<GanttView>` with positioned bars and completion fill.

---

## G — CAM Variance (variance table)

> **User:** "Show CAM cost and schedule variance for June."

```json
{
  "component": "variance_table",
  "title": "CAM Variance — June",
  "userIntent": "detail_lookup",
  "data": [
    { "cam": "J. Rivera", "bcwp": 420, "acwp": 455, "cv": -35, "sv": -10 },
    { "cam": "S. Okoye", "bcwp": 610, "acwp": 590, "cv": 20, "sv": 15 }
  ],
  "fields": { "label": "cam" },
  "columns": [
    { "key": "cam", "label": "CAM", "kind": "text" },
    { "key": "bcwp", "label": "BCWP", "kind": "plan" },
    { "key": "acwp", "label": "ACWP", "kind": "actual" },
    { "key": "cv", "label": "Cost Var", "kind": "variance" },
    { "key": "sv", "label": "Sched Var", "kind": "variance" }
  ],
  "metadata": { "source": "EVMS MCP", "explanation": "Variance table selected for plan-vs-actual detail by CAM." }
}
```

→ `<VarianceTable>` with ▲ green / ▼ red variance columns.

---

## H — Root-Cause Analysis (fishbone)

> **User:** "Why did the integration milestone slip?"

```json
{
  "component": "fishbone",
  "title": "Schedule Slip — Root Cause Analysis",
  "userIntent": "root_cause",
  "problem": "Integration milestone slipped 3 weeks",
  "data": [
    { "category": "People", "cause": "Two engineers reassigned mid-sprint" },
    { "category": "Process", "cause": "Late requirements baseline" },
    { "category": "Equipment", "cause": "Test rig double-booked" },
    { "category": "Suppliers", "cause": "Component delivered 10 days late" }
  ],
  "metadata": { "source": "RCA Workshop MCP", "explanation": "Fishbone selected to group causes by category." }
}
```

→ `<FishboneView>`, causes grouped into category bones.

---

## The pattern across all eight

Same `render_ui` tool, same `<AgentUIRenderer>`, same contract. Only the payload differs.
That uniformity is the deliverable: **the team adds value by adding renderers + teaching
the agent, never by re-plumbing the agent→UI path.**

Next: [rollout roadmap →](07-implementation-roadmap.md)
