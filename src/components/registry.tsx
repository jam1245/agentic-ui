/**
 * The component registry: the ONLY place that maps a `ComponentKind` to a React
 * renderer. This is the allow-list. If a component isn't here, the agent cannot
 * render it — which is exactly the guarantee a production UI wants.
 *
 * To add a visualization: add the type (contract/types.ts), its zod variant
 * (contract/schema.ts), a renderer, and one line here.
 */
import type { ComponentType } from "react";
import type { AgentUIPayload, ComponentKind } from "../contract";
import { DataTable } from "./renderers/DataTable";
import { LineChartView } from "./renderers/LineChartView";
import { BarChartView } from "./renderers/BarChartView";
import { KpiCardGrid } from "./renderers/KpiCardGrid";
import { RiskMatrix } from "./renderers/RiskMatrix";
import { TimelineView } from "./renderers/TimelineView";
import { GanttView } from "./renderers/GanttView";
import { VarianceTable } from "./renderers/VarianceTable";
import { FishboneView } from "./renderers/FishboneView";

// Each renderer receives the narrowed payload; we cast at the boundary because the
// registry key guarantees the discriminant matches.
type Renderer = ComponentType<{ payload: any }>;

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

/** The list of components the agent may choose from (see docs/04, docs/05). */
export const SUPPORTED_COMPONENTS = Object.keys(REGISTRY) as ComponentKind[];

export function getRenderer(payload: AgentUIPayload): Renderer {
  return REGISTRY[payload.component] ?? DataTable;
}
