# Testing this locally

Three tiers, easiest first. **Tier 1 needs no API key and no agent** — start there to see
both contracts working in your browser in under a minute.

---

## Tier 1 — The visual demo (no keys, no agent) ✅ start here

Proves **Contract 1** (rendering) and **Contract 2** (artifact context) with the real
React components and the real contract code. No CopilotKit, no Google ADK, no LLM.

```bash
npm install
npm run dev        # → http://localhost:5173
```

What you'll see:
- Tabs for every example payload (CPI trend, SPI bar, risk matrix, KPI cards, milestones,
  Gantt, CAM variance, fishbone) — each rendered by the same `<AgentUIRenderer>`.
- A **"What the chat agent remembers"** panel under each chart showing the exact compact
  digest that would be fed to the chat agent for follow-ups (summary + schema + filters +
  sample) — and proving the full dataset stays out of the prompt.

Requirements: Node 18+ (tested on Node 25). That's it.

---

## Tier 2 — The contracts under test (no keys) ✅ run in CI too

Runs the validation, fallback, and artifact round-trip tests on both sides.

```bash
# TypeScript / React contract
npm test            # 7 tests: payload validation, table fallback, artifact digest, rehydration
npm run typecheck   # whole React + scripts tree typechecks
npm run export:schema   # emits dist/agent-ui-payload.schema.json (the agent's tool schema)

# Python / ADK contract  (just needs pydantic, not the full ADK)
python3 -m pip install pydantic
python3 scripts/check_python_contract.py   # round-trips render → artifact → digest → rehydrate
```

These are the tests to wire into CI. They don't need a network or an LLM.

---

## Tier 3 — The live agent (needs a Gemini API key)

Runs the actual Google ADK agent so you can type questions and watch it choose components
and store artifacts.

```bash
cd agent
python3 -m pip install -r requirements.txt
export GOOGLE_API_KEY=...        # from aistudio.google.com/apikey  (or use Vertex AI)
adk web                          # opens the ADK dev UI; pick the program_analyst agent
# or headless:  adk run .
```

Try in sequence to see artifact-awareness:
1. `Show CPI trend for the last six months.`  → line chart, artifact stored
2. `Why did March dip?`                        → resolves "March" from the stored artifact
3. `Summarize program health.`                 → KPI cards
4. `Turn that into an executive summary.`       → "that" = the KPI artifact

> The ADK dev UI shows tool calls and session state, so you can watch `render_ui` fire and
> the `artifacts` key fill up in state — the clearest way to *see* Contract 2 working.

---

## Tier 4 — Full browser loop (ADK → self-hosted CopilotKit runtime → React)

Charts render **inside the chat** and follow-ups work end to end. Uses the open-source,
self-hosted `@copilotkit/runtime` — **no Copilot Cloud**. Three processes:

```
React chat (chat.html) ──/api/copilotkit──► CopilotKit runtime ──HttpAgent──► ADK (AG-UI)
   Vite :5173                                   Express :4000                  uvicorn :8000
```

**One command (after installs) runs all three:**

```bash
# 1. Python deps + key (once)
python3 -m pip install -r agent/requirements.txt
export GOOGLE_API_KEY=...          # aistudio.google.com/apikey, or configure Vertex AI

# 2. Node deps (once)  — npm install already pulled these
# 3. Launch agent + runtime + web together
npm run dev:full
```

Then open **http://localhost:5173/chat.html** and try, in order:
1. `Show CPI trend for the last six months.`  → a line chart renders in the chat
2. `Why did March dip?`                        → answered from the stored artifact
3. `Summarize program health.` → `Turn that into an executive summary.`

Run pieces individually if you prefer: `npm run dev:agent`, `npm run dev:runtime`,
`npm run dev:chat` (each in its own terminal).

**The moving parts (all in this repo, already typechecked):**
- [agent/serve.py](agent/serve.py) — exposes the ADK agent over AG-UI (`ag_ui_adk`)
- [server/copilotkit-runtime.ts](server/copilotkit-runtime.ts) — self-hosted runtime, `HttpAgent` → ADK
- [src/chat/ChatApp.tsx](src/chat/ChatApp.tsx) + [useAdkRenderUI.tsx](src/chat/useAdkRenderUI.tsx) — chat UI + generative-UI binding
- Vite proxies `/api/copilotkit` → the runtime (see [vite.config.ts](vite.config.ts))

**Notes for a secure/enterprise environment:**
- The runtime prints an anonymous-telemetry notice on boot. Disable it with
  `export COPILOTKIT_TELEMETRY_DISABLED=true` before `npm run dev:runtime`.
- The LLM key lives **only** in the ADK process; the runtime uses an empty adapter and
  never sees it. Point ADK at Vertex AI to keep traffic in your Google Cloud tenancy.
- `agent/serve.py` uses in-memory sessions for the demo. For real use, swap in a
  persistent session service so artifact context survives restarts / scales across pods.

> Version note: built and typechecked against `@copilotkit/runtime` 1.60.x,
> `@ag-ui/client` 0.0.57, `ag_ui_adk`. If you bump CopilotKit, re-run `npm run typecheck` —
> the AG-UI adapter import paths occasionally move between releases.

---

## What proves what

| You want to verify… | Run |
| --- | --- |
| Charts/tables/KPIs render from a payload | Tier 1 (`npm run dev`) |
| Bad payloads fall back to a table | Tier 2 (`npm test`) |
| The chat agent keeps a prompt-safe artifact digest | Tier 1 panel + Tier 2 |
| Full data is rehydrated on demand, not prompted | Tier 2 (artifact tests + Python script) |
| The agent picks the right component for a question | Tier 3 (`adk web`) |
| Follow-ups ("why did March dip?") work | Tier 3 |
| End-to-end in the browser | Tier 4 (your adapter wiring) |
