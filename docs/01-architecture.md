# 1. Conceptual Architecture

## The problem this solves

The team can already do this:

```
User question → Agent → Tool/MCP → Data returned → Table rendered
```

Data retrieval is **solved**. The open question is the *next hop*: when the right answer
is a line chart, a risk matrix, or a dashboard — not a table — **what does the agent send
to the front end, and how does the UI know what to do with it?**

The friction is an asymmetry:

| The agent knows | The React UI knows |
| --- | --- |
| the user's question | only the payload it receives |
| the business context | how to render registered components |
| the analytical intent | nothing about intent or meaning |
| what the data means | — |

So the architecture must **carry the agent's context across the boundary** in a form the
generic UI can act on.

## The pattern

```
User asks a question
  → Agent interprets intent
  → Agent calls MCP/data tool
  → Tool returns structured data (rows)
  → Agent selects a visualization pattern   ← the new step
  → Agent emits a structured UI payload      ← the contract
  → React renders the component
```

**The key rule:** the agent never generates the chart itself (no SVG, no React, no image).
It emits a **structured UI payload** that React already knows how to render.

## Why each piece is here

- **Internal Genesis LLM** — the reasoning engine. It interprets intent, picks the data
  tool, and chooses the visualization. The only LLM backend; no Google key.
  See [`05-backend-and-data-tools.md`](05-backend-and-data-tools.md).
- **Data tools / MCP** — the data-access layer behind the agent. Plain functions returning
  rows + source/filters; this is the part that already works today.
- **Transport (HTTP/JSON)** — the agent's payloads reach the browser over a simple
  `POST /api/chat`. The contract is transport-agnostic, so AG-UI events + a CopilotKit
  runtime can carry the *same* payload if you adopt that stack later
  ([`04-frontend-integration.md`](04-frontend-integration.md)).
- **React** — owns all rendering: a registry maps each component kind to a renderer.

## Responsibility split (the answer to "how much belongs where")

```
┌─────────────────────────────────────────────────────────────┐
│ AGENT (context-aware)                                         │
│  • interpret intent   • choose component   • map fields       │
│  • explain choice (metadata.explanation)                      │
└───────────────┬─────────────────────────────────────────────┘
                │  AgentUIPayload  (the contract — validated both sides)
                ▼
┌─────────────────────────────────────────────────────────────┐
│ REACT UI (generic)                                           │
│  • validate payload   • look up renderer   • draw pixels      │
│  • theming, axes, a11y, interactivity, fallback-to-table      │
└─────────────────────────────────────────────────────────────┘
```

The UI exposes a **fixed menu** of components (the registry / allow-list). The agent
chooses from that menu and supplies data + mapping + meaning. This keeps the UI generic
(add a renderer once, every agent can use it) while letting the agent drive the
experience dynamically (it decides which one and with what data).

## One payload, any transport

The contract is a single structured `AgentUIPayload` whose `component` field selects the
view. Adding a new chart type requires **no** transport change — just a renderer + a schema
entry. This repo delivers the payload over plain HTTP; the identical payload can ride AG-UI
events into a CopilotKit generative-UI action if you adopt that stack
([`04-frontend-integration.md`](04-frontend-integration.md)).

Next: [the payload contract →](02-payload-contract.md)
