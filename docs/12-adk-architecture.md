# 12. The Google ADK Architecture (foundational)

This is a **Google ADK project**. The agents, orchestration, tool-calling, and (next)
sub-agent delegation all use the [ADK](https://google.github.io/adk-docs/) framework — but
the **LLM is the internal Genesis model via LiteLLM**, an OpenAI-compatible endpoint. There
is **no Google Cloud, no Gemini, and no Google API key**. ADK is the framework; Genesis is
the brain. This is the part of the architecture everything else plugs into.

## Why ADK without Google models

ADK's `LlmAgent` takes any LiteLLM model. `agent/config/model_config.py`:

```python
from google.adk.models.lite_llm import LiteLlm

def get_model() -> LiteLlm:
    return LiteLlm(
        model=os.getenv("LLM_MODEL", "openai/gpt-oss-120b"),
        api_base=os.getenv("LLM_API_BASE", "https://api.ai.us.lmco.com/v1"),
        api_key=os.getenv("LLM_API_KEY"),
        ssl_verify=False,
    )
```

So the agent's reasoning **and tool-calling** run on Genesis. (This mirrors the proven
pattern in the companion `adk-project`.)

## The pieces

```
React (App.tsx) ── POST /api/chat ──► server/genesis_app.py ──► agent/runner.py (ADK Runner)
                                                                       │
                                            orchestrator (root_agent) routes via sub_agents
                                                                       │
                                       the chosen specialist (cam / risk / pm / rcca)
                                                                       │  ADK tool-calling (Genesis via LiteLLM)
        ┌──────────────────┬──────────────────────┬────────────────────────┬──────────────────────┐
        ▼                  ▼                      ▼                        ▼                      ▼
  data tools (rows)  render_chart(...)    get_artifact_data       call_*_assistant_v2     render_structured
                     builds+validates AgentUIPayload,             (Genesis specialist     (qualitative views,
                     stages into ADK session state                assistant)              e.g. fishbone)
                                          │
                runner reads staged payloads/artifacts from session state
                ──► { text, payloads, artifacts, context_used } ──► React renderers
```

- **`LlmAgent` (a lead/specialist agent)** — e.g. `agent/adk_agents/program_analyst/agent.py`. Brained by
  Genesis; given the data tools, `render_chart`, and the artifact-recall tools.
- **`render_chart` (the data→UI bridge)** — `agent/tools/render_tools.py`. An ADK function
  tool that takes `tool_context: ToolContext`, fetches authoritative rows from a data tool
  (so the model never fabricates numbers), builds + validates an `AgentUIPayload`
  ([Contract 1](02-payload-contract.md)), records an `ArtifactContext`
  ([Contract 2](09-artifact-aware-context.md)), and stages both into `tool_context.state`.
- **`runner.py`** — runs one turn through ADK's `Runner`, then reads the staged payloads /
  artifacts / context_used out of session state and returns them in the shape React already
  consumes. **React, the contract, and the renderers are unchanged** — ADK just replaces the
  old hand-rolled loop.
- **Data-aware follow-ups** — the agent calls `get_artifact_data` to pull a prior chart's
  rows and answer questions about them (drives the 🧠 badge); ADK's native loop lets the LLM
  genuinely reason and converse.

## Two execution paths (same response shape)

| Path | When | Engine |
| --- | --- | --- |
| **ADK + Genesis** | `LLM_API_KEY` set | the `LlmAgent` above — the real framework |
| **Deterministic** | `GENESIS_MOCK=1` or no key | `agent/genesis_agent.py` — an offline, LLM-free engine that computes charts/answers so demos and CI run with zero credentials |

Both return `{ text, payloads, artifacts, context_used }`, so the UI is identical. The
deterministic engine is the **offline fallback**, not the primary path.

## Orchestrator + specialist sub-agents (Phase 2 — built)

The default `root_agent` is now an **orchestrator** that routes each request to a specialist
sub-agent via ADK's native `sub_agents` delegation. `agent/runner.py` runs it.

```
orchestrator  (agent/adk_agents/orchestrator/agent.py)
  ├─ pm_agent    — program health, status, executive summaries, schedule  (call_pm_assistant_v2)   [default host]
  ├─ cam_agent   — EVM: CPI, SPI, cost/schedule variance, CAM variance     (call_cam_assistant_v2)
  ├─ risk_agent  — risk matrix, likelihood × impact, mitigation            (call_risk_assistant_v2)
  └─ rcca_agent  — root cause & corrective action, fishbone                (call_rcca_assistant_v2)
```

Each specialist is an `LlmAgent` (Genesis via LiteLLM) that can fetch its domain data,
**render charts** (`render_chart`, plus `render_structured` for qualitative views like a
fishbone), answer follow-ups (`get_artifact_data`), and **consult its pre-built Genesis
specialist assistant** through `agent/tools/external_assistant_tool.py`
(`call_*_assistant_v2`, which speaks the Genesis Assistants API). Because every sub-agent
writes to the same ADK session state, the `render_chart` → session-state → runner bridge
works no matter which agent handles the turn — React is unchanged.

**Plug and play:** add a specialist with one thin `agent.py` that calls
`make_specialist(...)` ([`_factory.py`](../agent/adk_agents/_factory.py)) and list it in the
orchestrator's `sub_agents`. Set the per-assistant ids in `.env`
(`CAM_ASSISTANT_ID`, `PM_ASSISTANT_ID`, `RISK_ASSISTANT_ID`, `RCCA_ASSISTANT_ID`).

This mirrors the `adk-project` orchestrator pattern.

← back to the [README](../README.md)
