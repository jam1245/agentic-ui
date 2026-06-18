# Testing this locally

**Everything runs with NO API key** thanks to an offline mock of the internal Genesis LLM
— then you flip a key to go live. No Google key is ever involved.

> **Windows / macOS / Linux:** runs the same on all three. Node, Python, and every `npm`
> script here are cross-platform (`concurrently` handles the multi-process one on Windows).
> Two small differences from the macOS examples:
> - **Use `python` (or `py`) instead of `python3`** if `python3` isn't on your PATH (common
>   on Windows).
> - **Don't `export` keys — put them in a `.env` file.** Copy `.env.example` to `.env` and
>   fill in `LLM_API_KEY` / `PM_ASSISTANT_ID`. Both the Python backend (`python-dotenv`) and
>   Vite load `.env` automatically, so you never need `export` (mac/Linux) or `set` /
>   `$env:` (Windows). On Windows use `copy .env.example .env` (cmd) or
>   `Copy-Item .env.example .env` (PowerShell) instead of `cp`.
>
> Prereqs everywhere: Node 18+ and Python 3.10+.

| Want to… | Run | Needs |
| --- | --- | --- |
| **The live page: Genesis chat + charts + context panel** | `npm run dev:genesis` → `/` | nothing (mock) → key to go live |
| Prove the pipeline in a terminal | `python3 scripts/genesis_demo.py --mock` | nothing |
| Browse every component (static) | `npm run dev` → Gallery tab | nothing |
| Run the contract tests | `npm test` | nothing |

---

## The live page (your internal Genesis LLM) — "the goal", working

One command starts the FastAPI Genesis backend **and** Vite, and opens a page with a live
chat on the left and an "under the hood" panel on the right.

```bash
python3 -m pip install -r agent/requirements.txt
npm install
npm run dev:genesis        # → http://localhost:5173/
```

Then, on the page:
1. Click **"Show CPI trend for the last six months."** → a line chart renders in the chat,
   and a card appears in the **Context** panel (data absorbed).
2. Click **"Why did March dip?"** → answered from that stored context; the assistant turn
   shows a **🧠 used context: CPI Trend** badge.
3. Click **"Summarize program health."** → KPI cards; Context panel grows.
4. Open the **Payload** tab to see the exact validated `AgentUIPayload` behind the last
   chart; the **Gallery** tab shows every component from static examples.

It runs in **mock mode** (no key) out of the box — `/api/health` reports `mode:"mock"`.

### Go live with the real Genesis LLM

```bash
# copy .env.example → .env and set LLM_API_KEY + PM_ASSISTANT_ID (loaded automatically)
#   macOS/Linux: cp .env.example .env   |   Windows: copy .env.example .env
npm run dev:genesis        # /api/health now reports mode:"genesis"
```

The key stays server-side (in the Python backend), never in the browser. Details:
[docs/10-genesis-internal-llm.md](docs/10-genesis-internal-llm.md).

---

## Terminal proof (no browser)

```bash
python3 scripts/genesis_demo.py --mock     # full conversation incl. "why did March dip?"
# or, with a key in .env:
python3 scripts/genesis_demo.py            # real Genesis, same output shape
```

Prints each validated payload and the artifact digests the agent retains.

---

## The contracts under test (CI-friendly, no keys)

```bash
# TypeScript / React contract
npm test            # payload validation, table fallback, artifact digest, rehydration
npm run typecheck
npm run export:schema   # emits dist/agent-ui-payload.schema.json

# Python contract (just needs pydantic)
python3 -m pip install pydantic
python3 scripts/check_python_contract.py   # render → artifact → digest → rehydrate
python3 scripts/genesis_demo.py --mock     # the agent loop, offline
```

These need no network and no LLM — wire them into CI.

---

## What proves what

| You want to verify… | Run |
| --- | --- |
| **Genesis LLM driving charts, end to end, in the browser** | `npm run dev:genesis` |
| Follow-ups answered from context ("why did March dip?") | the page, or `scripts/genesis_demo.py --mock` |
| Data is absorbed into chat context | the page's **Context** panel + the 🧠 badge |
| The exact contract payload behind a chart | the page's **Payload** tab |
| Every component renders from a payload | the page's **Gallery** tab / `npm run dev` |
| Bad payloads fall back to a table | `npm test` |
| Full data rehydrated on demand, not prompted | `npm test` + `scripts/check_python_contract.py` |
