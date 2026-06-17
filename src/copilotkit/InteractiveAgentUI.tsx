/**
 * Example of an INTERACTIVE agent-driven component that sends a result back to the
 * agent — the round trip that AG-UI's event protocol enables and CopilotKit exposes
 * via `renderAndWaitForResponse`.
 *
 * Use case: the agent renders a risk matrix; the user clicks a risk; that selection
 * flows back so the agent can fetch the mitigation plan and render a follow-up view.
 */
import { useCopilotAction } from "@copilotkit/react-core";
import { AgentUIRenderer } from "../components/AgentUIRenderer";
import { validatePayload } from "../contract";

export function useInteractiveAgentUI() {
  useCopilotAction({
    name: "render_ui_interactive",
    description:
      "Render a UI component and WAIT for the user's selection before continuing. " +
      "Use for drill-down: the user's chosen item (e.g. a risk, a task, a CAM) is returned to you.",
    parameters: [
      { name: "component", type: "string", required: true },
      { name: "title", type: "string", required: true },
      { name: "data", type: "object[]", required: true },
      { name: "fields", type: "object", required: false },
      { name: "metadata", type: "object", required: true },
    ],
    renderAndWaitForResponse: ({ args, respond, status }) => {
      const payload = validatePayload(args).payload;
      return (
        <div className="agent-ui-interactive" data-status={status}>
          <AgentUIRenderer raw={payload} />
          {status === "executing" && (
            <div className="agent-ui-actions">
              {payload.data.map((row, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => respond?.({ selected: row })}
                  className="agent-ui-drill-btn"
                >
                  {String(row.label ?? row.title ?? row.task ?? row.risk ?? `Item ${i + 1}`)}
                </button>
              ))}
            </div>
          )}
        </div>
      );
    },
  });
}
