/**
 * Runtime validation for the agent-to-UI contract.
 *
 * The agent is an LLM; its output is not guaranteed to match the TypeScript types.
 * Every payload that crosses the agent→UI boundary MUST be validated here before it
 * reaches a renderer. Invalid payloads degrade gracefully to a table rather than
 * crashing the UI — a malformed chart is still useful as raw data.
 *
 * We use zod because it gives us (a) a parser, (b) typed output, and (c) JSON-Schema
 * export for free — the same schema can be handed to the agent / the LLM as the
 * output schema, keeping the agent and UI in lockstep.
 */
import { z } from "zod";
import type { AgentUIPayload } from "./types";

const row = z.record(z.string(), z.unknown());

const metadata = z.object({
  source: z.string().min(1),
  explanation: z.string().optional(),
  filtersApplied: z.record(z.string(), z.unknown()).optional(),
  retrievedAt: z.string().optional(),
  notes: z.string().optional(),
});

const fields = z.object({
  x: z.string().optional(),
  y: z.string().optional(),
  groupBy: z.string().optional(),
  value: z.string().optional(),
  label: z.string().optional(),
});

const userIntent = z
  .enum([
    "trend_analysis",
    "comparison",
    "composition",
    "distribution",
    "ranking",
    "status_summary",
    "schedule",
    "root_cause",
    "detail_lookup",
  ])
  .optional();

const base = {
  artifactId: z.string().optional(),
  title: z.string().min(1),
  userIntent,
  data: z.array(row),
  fields: fields.optional(),
  metadata,
};

const status = z.enum(["good", "warning", "critical", "neutral"]);

export const payloadSchema = z.discriminatedUnion("component", [
  z.object({
    ...base,
    component: z.literal("table"),
    columns: z
      .array(
        z.object({
          key: z.string(),
          label: z.string(),
          align: z.enum(["left", "right", "center"]).optional(),
        }),
      )
      .optional(),
  }),
  z.object({
    ...base,
    component: z.literal("line_chart"),
    fields: fields.required({ x: true, y: true }),
    referenceLine: z.object({ value: z.number(), label: z.string().optional() }).optional(),
  }),
  z.object({
    ...base,
    component: z.literal("bar_chart"),
    fields: fields.required({ x: true, y: true }),
    orientation: z.enum(["vertical", "horizontal"]).optional(),
  }),
  z.object({
    ...base,
    component: z.literal("kpi_card"),
    data: z.array(row.and(z.object({ label: z.string(), value: z.union([z.number(), z.string()]), status: status.optional() }))),
  }),
  z.object({
    ...base,
    component: z.literal("risk_matrix"),
    fields: fields.required({ x: true, y: true }),
    scale: z.object({ likelihoodMax: z.number(), impactMax: z.number() }).optional(),
  }),
  z.object({
    ...base,
    component: z.literal("timeline"),
    data: z.array(row.and(z.object({ date: z.string(), title: z.string() }))),
  }),
  z.object({
    ...base,
    component: z.literal("gantt"),
    data: z.array(row.and(z.object({ task: z.string(), start: z.string(), end: z.string() }))),
  }),
  z.object({
    ...base,
    component: z.literal("variance_table"),
    fields: fields.required({ label: true }),
    columns: z.array(
      z.object({
        key: z.string(),
        label: z.string(),
        kind: z.enum(["plan", "actual", "variance", "text"]),
      }),
    ),
  }),
  z.object({
    ...base,
    component: z.literal("fishbone"),
    problem: z.string(),
    data: z.array(row.and(z.object({ category: z.string(), cause: z.string() }))),
  }),
]);

export interface ValidationResult {
  ok: boolean;
  /** Always present: either the validated payload or a safe table fallback. */
  payload: AgentUIPayload;
  /** Populated when validation failed and we fell back to a table. */
  error?: string;
}

/**
 * Validate an arbitrary agent output. On failure, salvage whatever `data`/`title`
 * we can and render it as a table so the user still sees their numbers.
 */
export function validatePayload(raw: unknown): ValidationResult {
  const parsed = payloadSchema.safeParse(raw);
  if (parsed.success) {
    return { ok: true, payload: parsed.data as AgentUIPayload };
  }

  const obj = (raw ?? {}) as Record<string, unknown>;
  const fallback: AgentUIPayload = {
    component: "table",
    title: typeof obj.title === "string" ? obj.title : "Results",
    data: Array.isArray(obj.data) ? (obj.data as Record<string, unknown>[]) : [],
    metadata: {
      source: "unknown",
      explanation: "Rendered as a table because the agent payload failed validation.",
      notes: parsed.error.issues.map((i) => `${i.path.join(".")}: ${i.message}`).join("; "),
    },
  };
  return { ok: false, payload: fallback, error: parsed.error.message };
}
