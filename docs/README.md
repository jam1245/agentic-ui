# Implementation Guide — read in order

This folder is a step-by-step guide to the agent-to-UI contract and the artifact-aware
chat. Each page ends with a **Next →** link, so you can start at the top and click through.

**Do this first:** run the demo so the rest is concrete —
[`../TESTING.md`](../TESTING.md) → `npm run dev:genesis`, then click the chips.

| # | Page | What you'll learn |
| --- | --- | --- |
| 1 | [Architecture](01-architecture.md) | why the agent emits a *payload*, not a chart; who owns what |
| 2 | [Payload contract (Contract 1)](02-payload-contract.md) | the `AgentUIPayload` schema, field by field, and the rationale |
| 3 | [React rendering](03-react-rendering.md) | the registry + one generic `<AgentUIRenderer>` |
| 4 | [Frontend integration](04-frontend-integration.md) | how a payload reaches React (+ optional CopilotKit/AG-UI) |
| 5 | [Backend & data tools](05-backend-and-data-tools.md) | data tools / MCP + the hybrid agent loop |
| 6 | [Worked examples](06-examples.md) | the same contract across 8 program-management scenarios |
| 7 | [Implementation roadmap](07-implementation-roadmap.md) | crawl/walk/run rollout + anti-patterns |
| 8 | [Validation & fallbacks](08-validation-and-fallbacks.md) | validate both sides; degrade to a table, never crash |
| 9 | [Artifact-aware context (Contract 2)](09-artifact-aware-context.md) | how charts stay in chat context for follow-ups |
| 10 | [Run on the internal Genesis LLM](10-genesis-internal-llm.md) | the LLM end to end + a per-prompt demo walkthrough |
| 11 | [Extend: add a visualization](11-add-a-visualization.md) | a copy-pasteable, 6-step worked example |

The two ideas the whole guide is built around:

1. **Contract 1 — agent-to-UI:** the agent returns a structured `AgentUIPayload`; a generic
   React renderer turns it into the right component. (Pages 1–6, 8)
2. **Contract 2 — artifact-to-agent:** every rendered chart is also stored as an
   `ArtifactContext`, so the chat stays data-aware and answers follow-ups. (Page 9)

Everything runs on the internal **Genesis** LLM — no Google or other API key (Page 10).
