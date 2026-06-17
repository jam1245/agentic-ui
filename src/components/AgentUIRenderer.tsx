/**
 * The single entry point the rest of your app uses.
 *
 *   <AgentUIRenderer raw={payloadFromAgent} />
 *
 * It validates the payload (falling back to a table on failure), looks up the
 * renderer in the registry, and wraps it with a title + provenance/explanation
 * footer so every agent-driven visualization is self-describing.
 */
import { useMemo } from "react";
import type { AgentUIPayload } from "../contract";
import { validatePayload } from "../contract";
import { getRenderer } from "./registry";

interface Props {
  /** Unvalidated payload straight from the agent / CopilotKit action args. */
  raw: unknown;
  /** Skip validation if the caller already validated (e.g. server-side). */
  prevalidated?: AgentUIPayload;
}

export function AgentUIRenderer({ raw, prevalidated }: Props) {
  const { payload, ok, error } = useMemo(() => {
    if (prevalidated) return { payload: prevalidated, ok: true as const, error: undefined };
    return validatePayload(raw);
  }, [raw, prevalidated]);

  const Renderer = getRenderer(payload);

  return (
    <section className="agent-ui" data-component={payload.component}>
      <header className="agent-ui-header">
        <h3 className="agent-ui-title">{payload.title}</h3>
        {!ok && <span className="agent-ui-badge agent-ui-badge--fallback">fallback: table</span>}
      </header>

      <div className="agent-ui-body">
        <Renderer payload={payload} />
      </div>

      <footer className="agent-ui-footer">
        {payload.metadata.explanation && (
          <span className="agent-ui-explanation">{payload.metadata.explanation}</span>
        )}
        <span className="agent-ui-source">Source: {payload.metadata.source}</span>
        {error && <span className="agent-ui-error" title={error}>⚠ payload validation failed</span>}
      </footer>
    </section>
  );
}
