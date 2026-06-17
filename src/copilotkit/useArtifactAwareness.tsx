/**
 * Makes rendered artifacts visible to the MAIN CHAT AGENT so it can answer follow-ups
 * ("why did March dip?", "summarize that for leadership", "compare this to SPI").
 *
 * Two CopilotKit primitives do the work:
 *   1. useCopilotReadable  — feeds the agent the COMPACT digests every turn (summary +
 *      schema + filters + sample). This is the prompt-budget-safe context. NEVER put full
 *      datasets here.
 *   2. useCopilotAction("get_artifact_data") — lets the agent REHYDRATE the full rows for
 *      a specific artifact only when a follow-up actually needs them.
 *
 * This is the front-end expression of the storage strategy: summary in the prompt, full
 * data on demand. (In production the agent can also read these digests from the backend
 * session store / ADK state — see docs/09.)
 */
import { useCopilotAction, useCopilotReadable } from "@copilotkit/react-core";
import { artifactRegistry, useArtifactDigests } from "../store/artifactRegistry";

export function useArtifactAwareness() {
  const digests = useArtifactDigests();

  // 1. Compact, always-on context. The agent sees titles, summaries, schemas, filters,
  //    and artifactIds for everything rendered this session — enough to resolve "this"/
  //    "that" and decide whether it needs the full data.
  useCopilotReadable({
    description:
      "Artifacts already rendered in this conversation (charts, tables, KPI cards, etc.). " +
      "Use these to answer follow-up questions about previously shown visualizations. " +
      "Each has an artifactId; call get_artifact_data(artifactId) if you need the full rows.",
    value: digests,
  });

  // 2. On-demand rehydration. Keeps full datasets OUT of the standing context; the agent
  //    pulls rows for one artifact only when the follow-up requires row-level detail
  //    (e.g. "why did March dip?" → fetch the CPI rows → inspect March).
  useCopilotAction({
    name: "get_artifact_data",
    description:
      "Retrieve the full underlying data for a previously rendered artifact by its artifactId. " +
      "Call this only when a follow-up needs row-level detail not in the summary.",
    parameters: [{ name: "artifactId", type: "string", required: true }],
    handler: ({ artifactId }) => {
      const artifact = artifactRegistry.get(artifactId);
      if (!artifact) return { error: `No artifact with id ${artifactId}` };
      return {
        artifactId,
        title: artifact.title,
        fields: artifact.fields,
        filtersApplied: artifact.filtersApplied,
        // The full rows. If this client cache misses (e.g. after reload), use dataRef to
        // re-query the source tool instead — see docs/09 "rehydration".
        data: artifact.fullData ?? artifact.dataSample ?? [],
        dataRef: artifact.dataRef,
      };
    },
  });
}
