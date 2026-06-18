# 8. Validation, Fallbacks & The Important Nuance

> The example repo proves the *concept*. A production stack still needs a deliberate
> integration contract. This page covers the parts that turn the demo into something
> you can ship.

## The trust boundary

The thing producing payloads is an **LLM**. Its output is not guaranteed to match your
types, even with a JSON Schema attached. So validate on **both** sides:

```
Genesis agent → pydantic validate → POST /api/chat → validatePayload (zod) → render
                     │                                       │
                     └─ raises → loop / fall back            └─ fails → table fallback
```

- **Server-side (pydantic, [`genesis_agent.py`](../agent/genesis_agent.py)):** assembles
  the payload from real tool rows + the model's render spec and validates before returning;
  a bad component degrades to a table rather than reaching the browser broken.
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
| How are payloads delivered? | Over `POST /api/chat` as JSON ([04](04-frontend-integration.md)); the same payload can ride AG-UI/CopilotKit unchanged. |
| How is data-source state preserved? | Data tools return source-tagged rows; `metadata.source`/`filtersApplied` travel in the payload so provenance survives to the UI; the artifact registry keeps full rows for rehydration ([09](09-artifact-aware-context.md)). |

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

Next: [artifact-aware context (Contract 2) →](09-artifact-aware-context.md)
