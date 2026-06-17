# 8. Validation, Fallbacks & The Important Nuance

> The example repo proves the *concept*. A production stack still needs a deliberate
> integration contract. This page covers the parts that turn the demo into something
> you can ship.

## The trust boundary

The thing producing payloads is an **LLM**. Its output is not guaranteed to match your
types, even with a JSON Schema attached. So validate on **both** sides:

```
agent → render_ui (pydantic validate) → AG-UI → CopilotKit → validatePayload (zod) → render
            │                                                      │
            └─ raises → agent self-corrects in-turn               └─ fails → table fallback
```

- **Server-side (pydantic, [`ui_tools.py`](../agent/ui_tools.py)):** catches most errors
  early and lets the agent *fix and retry* within the same run — the user never sees it.
- **Client-side (zod, [`schema.ts`](../src/contract/schema.ts)):** the backstop. Anything
  that slips through renders as a **table** with the original data preserved, plus a
  visible "fallback" badge and the validation error in the footer.

```ts
export function validatePayload(raw: unknown): ValidationResult {
  const parsed = payloadSchema.safeParse(raw);
  if (parsed.success) return { ok: true, payload: parsed.data };
  // salvage data + title so the user still sees their numbers
  return { ok: false, payload: { component: "table", title: ..., data: ..., metadata: {...} },
           error: parsed.error.message };
}
```

**Principle:** a malformed chart should never be worse than the table you have today. A
failed `line_chart` becomes a table of the same rows — degraded, never broken.

## The decisions you must make deliberately

The team's own list, answered:

| Decision | Recommendation |
| --- | --- |
| Which components are allowed? | The registry in [`registry.tsx`](../src/components/registry.tsx) **is** the allow-list. The agent is told exactly this set; it cannot invent another. |
| What schema does each component expect? | [`contract/types.ts`](../src/contract/types.ts) + zod variants in [`schema.ts`](../src/contract/schema.ts). One file, mirrored in pydantic. |
| How is data validated? | zod (client) + pydantic (server), from one exported JSON Schema. |
| How do errors fall back? | Always to `table`, data preserved, error surfaced in footer. |
| Direct payload vs registered UI tool? | Registered UI tool (`render_ui`) — Pattern A. Keeps the contract enforced at the boundary and lets the UI advertise its menu. |
| How do AG-UI/CopilotKit carry payloads? | The `render_ui` tool call becomes an AG-UI event; CopilotKit's `useCopilotAction("render_ui").render` receives the args and renders. See [04](04-copilotkit-agui-integration.md). |
| How is ADK/MCP state preserved? | Data tools return source-tagged rows; `metadata.source`/`filtersApplied` travel in the payload so provenance survives to the UI. Durable selections go through CopilotKit shared state, not render payloads. |

## Defensive practices

- **Cap `data` size.** Instruct the agent to aggregate; reject payloads over N rows
  server-side (a chart of 10k points is a bug, not a feature).
- **Sanitize strings.** Renderers must treat all string values as untrusted text (never
  `dangerouslySetInnerHTML`). The reference renderers only set text content.
- **Pin the component enum.** Validate `component` against the registry keys; an unknown
  kind → table fallback (covered by [the test](../src/contract/schema.test.ts)).
- **Log every render decision.** `{question, component, userIntent, ok, fellBack}` is your
  signal for prompt tuning and for spotting components the agent over/under-uses.
- **Version the contract.** Add a `contractVersion` if you expect breaking changes; let the
  UI reject or adapt unknown versions.

## What "done" looks like

1. One contract, one source of truth, mirrored in TS + Python, exported as JSON Schema.
2. A registry/allow-list the agent is told about verbatim.
3. Validation on both sides with table fallback.
4. An agent instruction that maps **intent → component**, plus a small eval set.
5. Telemetry on render decisions.

At that point the team's recurring work is: *add a renderer, add a schema variant, teach
the agent one rule.* The agent→UI path itself never needs to change again.

← back to the [README](../README.md)
