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
  → React / CopilotKit renders the component
```

**The key rule:** the agent never generates the chart itself (no SVG, no React, no image).
It calls a **UI-rendering tool** (`render_ui`) or emits a **structured UI payload** that
React already knows how to render.

## Why each piece of the stack is here

- **Google ADK** — orchestrates the agent and its tools. ADK tools have structured,
  typed inputs and outputs, which is exactly what we need: one set of tools for *data*,
  one tool for *UI intent*. See [`05-google-adk-tools.md`](05-google-adk-tools.md).
- **MCP** — the data-access layer behind the data tools. Unchanged from today; this is the
  part that already works.
- **AG-UI** — standardizes agent-to-frontend communication as an **event protocol**. The
  `render_ui` payload and any user interaction travel over AG-UI events, so the transport
  is the same whether the UI is display-only or interactive.
- **CopilotKit** — the React integration that turns AG-UI events into rendered components.
  Its **generative UI** feature lets you register a React renderer for a tool/action; when
  the agent calls it, CopilotKit renders your component with the args as props.
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

## Two valid transport choices

Both keep the *contract* identical; they differ only in how the payload is delivered:

1. **Single `render_ui` action** (recommended to start). One ADK tool / one CopilotKit
   action whose argument *is* the `AgentUIPayload`. Adding a new chart type requires **no**
   new tool/action — just a renderer + a schema entry. Fewer moving parts, one thing for
   the LLM to learn.
2. **One action per component** (`line_chart`, `risk_matrix`, …). More explicit
   per-component schemas and discoverability, but N tools to maintain and N signatures for
   the model to learn. Good once your component catalog is stable.

This guide implements **option 1** and documents option 2 in
[`04-copilotkit-agui-integration.md`](04-copilotkit-agui-integration.md).

Next: [the payload contract →](02-payload-contract.md)
