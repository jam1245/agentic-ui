/**
 * Realistic program-management example payloads. These are the canonical "what the
 * agent emits" samples referenced throughout the docs and used by the demo App and
 * the contract tests. Each is a valid `AgentUIPayload`.
 */
import type { AgentUIPayload } from "../contract";

export const cpiTrend: AgentUIPayload = {
  component: "line_chart",
  title: "CPI Trend — Last 6 Months",
  userIntent: "trend_analysis",
  data: [
    { month: "Jan", cpi: 0.92 },
    { month: "Feb", cpi: 0.95 },
    { month: "Mar", cpi: 0.98 },
    { month: "Apr", cpi: 0.97 },
    { month: "May", cpi: 0.99 },
    { month: "Jun", cpi: 1.01 },
  ],
  fields: { x: "month", y: "cpi" },
  referenceLine: { value: 1.0, label: "Target" },
  metadata: {
    source: "EVMS MCP",
    explanation: "Line chart selected because the user asked for a trend over time.",
    filtersApplied: { program: "P-117", months: 6 },
  },
};

export const spiByControlAccount: AgentUIPayload = {
  component: "bar_chart",
  title: "SPI by Control Account",
  userIntent: "comparison",
  data: [
    { account: "CA-100", spi: 1.04 },
    { account: "CA-200", spi: 0.91 },
    { account: "CA-300", spi: 1.0 },
    { account: "CA-400", spi: 0.86 },
  ],
  fields: { x: "account", y: "spi" },
  metadata: { source: "EVMS MCP", explanation: "Bar chart selected to compare SPI across discrete control accounts." },
};

export const riskMatrix: AgentUIPayload = {
  component: "risk_matrix",
  title: "Top Program Risks",
  userIntent: "distribution",
  data: [
    { risk: "Supplier delay", likelihood: 4, impact: 5 },
    { risk: "Staffing gap", likelihood: 3, impact: 4 },
    { risk: "Test rig availability", likelihood: 2, impact: 3 },
    { risk: "Scope creep", likelihood: 4, impact: 2 },
  ],
  fields: { x: "likelihood", y: "impact", label: "risk" },
  scale: { likelihoodMax: 5, impactMax: 5 },
  metadata: { source: "Risk Register MCP", explanation: "Risk matrix selected to position risks by likelihood × impact." },
};

export const programKpis: AgentUIPayload = {
  component: "kpi_card",
  title: "Program Health Summary",
  userIntent: "status_summary",
  data: [
    { label: "CPI", value: 0.94, status: "warning" },
    { label: "SPI", value: 1.02, status: "good" },
    { label: "Open Risks", value: 12, status: "warning" },
    { label: "EAC Variance", value: "-$1.2M", status: "critical" },
  ],
  metadata: { source: "EVMS MCP", explanation: "KPI cards selected for a headline health summary across metrics." },
};

export const milestones: AgentUIPayload = {
  component: "timeline",
  title: "Upcoming Milestones",
  userIntent: "schedule",
  data: [
    { date: "2026-07-15", title: "PDR", description: "Preliminary Design Review", status: "good" },
    { date: "2026-09-01", title: "CDR", description: "Critical Design Review", status: "neutral" },
    { date: "2026-11-30", title: "TRR", description: "Test Readiness Review", status: "warning" },
  ],
  metadata: { source: "IMS MCP", explanation: "Timeline selected for chronological milestone review." },
};

export const scheduleGantt: AgentUIPayload = {
  component: "gantt",
  title: "Integration & Test Schedule",
  userIntent: "schedule",
  data: [
    { task: "Subsystem integration", start: "2026-07-01", end: "2026-08-15", percentComplete: 60, status: "good" },
    { task: "Environmental test", start: "2026-08-10", end: "2026-09-20", percentComplete: 10, status: "warning" },
    { task: "Acceptance test", start: "2026-09-15", end: "2026-10-30", percentComplete: 0, status: "neutral" },
  ],
  metadata: { source: "IMS MCP", explanation: "Gantt selected to show overlapping task durations." },
};

export const camVariance: AgentUIPayload = {
  component: "variance_table",
  title: "CAM Variance — June",
  userIntent: "detail_lookup",
  data: [
    { cam: "J. Rivera", bcwp: 420, acwp: 455, cv: -35, sv: -10 },
    { cam: "S. Okoye", bcwp: 610, acwp: 590, cv: 20, sv: 15 },
    { cam: "L. Tan", bcwp: 300, acwp: 360, cv: -60, sv: -25 },
  ],
  fields: { label: "cam" },
  columns: [
    { key: "cam", label: "CAM", kind: "text" },
    { key: "bcwp", label: "BCWP", kind: "plan" },
    { key: "acwp", label: "ACWP", kind: "actual" },
    { key: "cv", label: "Cost Var", kind: "variance" },
    { key: "sv", label: "Sched Var", kind: "variance" },
  ],
  metadata: { source: "EVMS MCP", explanation: "Variance table selected for plan-vs-actual detail by CAM." },
};

export const rootCause: AgentUIPayload = {
  component: "fishbone",
  title: "Schedule Slip — Root Cause Analysis",
  userIntent: "root_cause",
  problem: "Integration milestone slipped 3 weeks",
  data: [
    { category: "People", cause: "Two engineers reassigned mid-sprint" },
    { category: "People", cause: "Onboarding ramp for new hire" },
    { category: "Process", cause: "Late requirements baseline" },
    { category: "Equipment", cause: "Test rig double-booked" },
    { category: "Suppliers", cause: "Component delivered 10 days late" },
  ],
  metadata: { source: "RCA Workshop MCP", explanation: "Fishbone selected to group causes by category for root-cause analysis." },
};

export const ALL_EXAMPLES: { key: string; payload: AgentUIPayload }[] = [
  { key: "CPI trend", payload: cpiTrend },
  { key: "SPI bar", payload: spiByControlAccount },
  { key: "Risk matrix", payload: riskMatrix },
  { key: "KPI summary", payload: programKpis },
  { key: "Milestones", payload: milestones },
  { key: "Gantt", payload: scheduleGantt },
  { key: "CAM variance", payload: camVariance },
  { key: "Root cause", payload: rootCause },
];
