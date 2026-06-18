/**
 * The SECOND contract: artifact-to-agent context.
 *
 * The rendering payload (AgentUIPayload) tells React *how to draw* an artifact. This
 * contract tells the **main chat agent** *what the artifact means* so it can answer
 * follow-ups like "why did March dip?", "summarize this for leadership", "turn that into
 * action items" — without re-deriving everything from scratch.
 *
 * A rendered chart must not be a dead end. Every render produces ONE AgentUIPayload (for
 * the UI) AND ONE ArtifactContext (for the conversation), sharing the same `artifactId`.
 *
 * STORAGE STRATEGY (the key design decision — see docs/09):
 *   We do NOT stuff full datasets into the LLM prompt every turn. Instead each
 *   ArtifactContext carries:
 *     - summaryForFutureTurns  (1-2 sentences — THIS is what goes in the prompt)
 *     - fields / schema + filtersApplied  (cheap, also in the prompt)
 *     - dataSample             (first few rows — enough to reason about shape)
 *     - dataRef                (a pointer to rehydrate fullData on demand)
 *   `fullData` lives in the registry/session store, retrieved only when a follow-up
 *   genuinely needs the raw rows.
 */
import type { AgentUIPayload, ComponentKind } from "./types";

export type ArtifactType = ComponentKind;

export interface ArtifactContext {
  artifactId: string;
  artifactType: ArtifactType;
  title: string;
  /** The user's question that produced this artifact — anchors "this"/"that" references. */
  originalUserQuestion: string;
  /** The data tool that produced the rows, e.g. "evms_mcp.get_cpi_history". */
  sourceTool: string;
  /** The system of record, e.g. "EVMS". */
  sourceSystem?: string;
  /** Opaque pointer used to rehydrate fullData later (cache key, query hash, URI). */
  dataRef?: string;
  /** A few representative rows — enough for the agent to reason about shape cheaply. */
  dataSample?: Record<string, unknown>[];
  /** The complete dataset. Stored in the registry; NOT injected into the prompt. */
  fullData?: Record<string, unknown>[];
  /** Field-role mapping (x/y/groupBy/value/label) used to render. */
  fields: Record<string, string>;
  filtersApplied?: Record<string, unknown>;
  assumptions?: string[];
  /** Why the agent chose this view / what it interpreted the request to be. */
  agentInterpretation: string;
  /** 1-2 sentence takeaway. THIS string is what gets injected into future prompts. */
  summaryForFutureTurns: string;
  createdAt: string;
}

/** How many rows to keep as the inline sample. Keep small — this is prompt-budget. */
const SAMPLE_SIZE = 5;

let _counter = 0;
export function newArtifactId(component: ComponentKind): string {
  _counter += 1;
  return `artifact_${component}_${Date.now().toString(36)}_${_counter}`;
}

/**
 * Normalize a rendering payload into an ArtifactContext. The agent supplies the things
 * only it knows (the original question, its interpretation, the summary); everything else
 * is derived from the payload so the two contracts cannot drift.
 */
export function toArtifactContext(
  payload: AgentUIPayload,
  ctx: {
    originalUserQuestion: string;
    sourceTool: string;
    summaryForFutureTurns: string;
    sourceSystem?: string;
    dataRef?: string;
    assumptions?: string[];
  },
): ArtifactContext {
  const artifactId = payload.artifactId ?? newArtifactId(payload.component);
  return {
    artifactId,
    artifactType: payload.component,
    title: payload.title,
    originalUserQuestion: ctx.originalUserQuestion,
    sourceTool: ctx.sourceTool,
    sourceSystem: ctx.sourceSystem ?? payload.metadata.source,
    dataRef: ctx.dataRef,
    dataSample: payload.data.slice(0, SAMPLE_SIZE),
    fullData: payload.data,
    fields: (payload.fields as Record<string, string>) ?? {},
    filtersApplied: payload.metadata.filtersApplied,
    assumptions: ctx.assumptions,
    agentInterpretation:
      ctx.summaryForFutureTurns && payload.metadata.explanation
        ? payload.metadata.explanation
        : payload.metadata.explanation ?? ctx.summaryForFutureTurns,
    summaryForFutureTurns: ctx.summaryForFutureTurns,
    createdAt: new Date().toISOString(),
  };
}

/**
 * The compact, prompt-safe projection of an artifact. THIS is what you feed the chat
 * agent each turn (from the session store) — never the full dataset.
 */
export interface ArtifactDigest {
  artifactId: string;
  artifactType: ArtifactType;
  title: string;
  originalUserQuestion: string;
  summary: string;
  fields: Record<string, string>;
  filtersApplied?: Record<string, unknown>;
  rowCount: number;
  dataSample?: Record<string, unknown>[];
  hasFullData: boolean;
  createdAt: string;
}

export function toDigest(a: ArtifactContext): ArtifactDigest {
  return {
    artifactId: a.artifactId,
    artifactType: a.artifactType,
    title: a.title,
    originalUserQuestion: a.originalUserQuestion,
    summary: a.summaryForFutureTurns,
    fields: a.fields,
    filtersApplied: a.filtersApplied,
    rowCount: a.fullData?.length ?? a.dataSample?.length ?? 0,
    dataSample: a.dataSample,
    hasFullData: Boolean(a.fullData?.length) || Boolean(a.dataRef),
    createdAt: a.createdAt,
  };
}
