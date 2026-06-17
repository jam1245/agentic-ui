/**
 * Tier-4 generative-UI binding for the ADK backend.
 *
 * The agent's `render_ui` tool runs SERVER-SIDE in ADK (it validates the payload and
 * stores the ArtifactContext in session state). CopilotKit surfaces that tool call to the
 * browser; this hook matches it by name and DRAWS the chart from the call's arguments.
 *
 * Why this differs from `useAgentUI` (the standalone hook):
 *   - useAgentUI is for a pure-frontend CopilotKit agent — render_ui is a FRONTEND tool
 *     with flat params, and the browser owns artifact storage.
 *   - useAdkRenderUI is for the ADK backend — render_ui args are nested under `payload`
 *     (matching agent/ui_tools.py: render_ui(payload, original_user_question, ...)), and
 *     ADK session state is the source of truth for artifacts. We still mirror the artifact
 *     into the client registry so any client-side UI can read it, but the agent recalls
 *     follow-ups via its own backend list_artifacts / get_artifact_data tools.
 */
import { useCopilotAction } from "@copilotkit/react-core";
import { AgentUIRenderer } from "../components/AgentUIRenderer";
import { newArtifactId, toArtifactContext, validatePayload } from "../contract";
import { artifactRegistry } from "../store/artifactRegistry";

export function useAdkRenderUI() {
  useCopilotAction({
    // Matches the ADK backend tool name. `render`-only (no handler): execution happens in
    // ADK; the browser just renders the result.
    name: "render_ui",
    available: "disabled", // the agent decides to call it; we never invoke it from the UI
    render: ({ args }) => {
      const a = (args ?? {}) as Record<string, unknown>;
      // ADK passes the rendering payload nested under `payload`; tolerate a flat shape too.
      const raw = (a.payload ?? a) as unknown;
      const { payload } = validatePayload(raw);
      if (!payload.artifactId) payload.artifactId = newArtifactId(payload.component);

      // Mirror into the client registry (ADK session state remains source of truth).
      artifactRegistry.upsert(
        toArtifactContext(payload, {
          originalUserQuestion: String(a.original_user_question ?? ""),
          summaryForFutureTurns: String(a.summary_for_future_turns ?? payload.metadata.explanation ?? ""),
          sourceTool: String(a.source_tool ?? payload.metadata.source ?? "unknown"),
        }),
      );

      return <AgentUIRenderer prevalidated={payload} raw={raw} />;
    },
  });
}
