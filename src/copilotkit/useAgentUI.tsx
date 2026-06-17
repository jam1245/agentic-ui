/**
 * CopilotKit integration: register ONE generative-UI action that the agent calls to
 * render any approved visualization.
 *
 * Two patterns exist for agent-driven UI in CopilotKit. We use Pattern A by default
 * and document Pattern B; see docs/04-copilotkit-agui-integration.md.
 *
 *   Pattern A — single "render_ui" action (recommended to start)
 *     The agent calls one action whose argument IS the AgentUIPayload. The front end
 *     validates and dispatches through the registry. Adding a chart type requires NO
 *     front-end action changes — only a renderer + schema entry. The contract is the
 *     interface; the action is just the transport.
 *
 *   Pattern B — one CopilotKit action per component
 *     `useCopilotAction({ name: "line_chart", parameters: [...] })` etc. More explicit
 *     per-component validation and discoverability, but N actions to maintain and the
 *     LLM must learn N tool signatures. Good once the catalog stabilizes.
 *
 * This hook implements Pattern A. `renderAndWaitForResponse` lets a component send
 * user interaction (drill-down clicks, edits) back into the agent run — that round
 * trip is what AG-UI's event protocol carries under the hood.
 */
import { useCopilotAction } from "@copilotkit/react-core";
import { AgentUIRenderer } from "../components/AgentUIRenderer";
import { SUPPORTED_COMPONENTS } from "../components/registry";
import { newArtifactId, toArtifactContext, validatePayload } from "../contract";
import { artifactRegistry } from "../store/artifactRegistry";

export function useAgentUI() {
  useCopilotAction({
    name: "render_ui",
    description:
      "Render a rich UI component for the user AND register it as a conversational artifact. " +
      "Call this instead of replying with a table in text. " +
      "Choose the component that best matches the user's analytical intent. " +
      `Allowed components: ${SUPPORTED_COMPONENTS.join(", ")}.`,
    // We accept the whole payload as a single structured arg. The JSON Schema the LLM
    // sees should be generated from contract/schema.ts (see scripts/export-schema.ts)
    // so the agent and UI never drift.
    parameters: [
      { name: "component", type: "string", required: true, description: "One of the allowed component kinds." },
      { name: "title", type: "string", required: true },
      { name: "userIntent", type: "string", required: false },
      { name: "data", type: "object[]", required: true, description: "Row objects to visualize." },
      { name: "fields", type: "object", required: false, description: "x/y/groupBy/value/label key mapping." },
      { name: "metadata", type: "object", required: true, description: "{ source, explanation, filtersApplied }" },
      // Artifact-awareness fields — what the agent knows that the payload alone doesn't.
      { name: "originalUserQuestion", type: "string", required: true, description: "The user's question that produced this artifact." },
      { name: "summaryForFutureTurns", type: "string", required: true, description: "1-2 sentence takeaway injected into future prompts." },
      { name: "sourceTool", type: "string", required: false, description: "Data tool that produced the rows, e.g. evms_mcp.get_cpi_history." },
    ],
    // `render` = display-only. Use `renderAndWaitForResponse` when the component must
    // return a value to the agent (e.g. user picks a risk to drill into).
    render: ({ args }) => {
      const { payload } = validatePayload(args);
      // Ensure a stable id ties the rendered artifact to its stored context.
      if (!payload.artifactId) payload.artifactId = newArtifactId(payload.component);

      // SECOND CONTRACT: normalize + store so the chat agent stays data-aware.
      const a = args as Record<string, unknown>;
      artifactRegistry.upsert(
        toArtifactContext(payload, {
          originalUserQuestion: String(a.originalUserQuestion ?? ""),
          summaryForFutureTurns: String(a.summaryForFutureTurns ?? payload.metadata.explanation ?? ""),
          sourceTool: String(a.sourceTool ?? payload.metadata.source ?? "unknown"),
        }),
      );

      return <AgentUIRenderer prevalidated={payload} raw={args} />;
    },
  });
}
