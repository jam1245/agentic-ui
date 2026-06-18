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
React (App.tsx) ── POST /api/chat ──► server/genesis_app.py
                                          │
                                   agent/runner.py  (ADK Runner)
                                          │
                        agent/adk_agents/program_analyst/agent.py
                        root_agent = LlmAgent(model=get_model(), tools=[…])
                                          │  ADK tool-calling loop (on Genesis via LiteLLM)
        ┌─────────────────────────────────┼───────────────────────────────────┐
        ▼                                  ▼                                    ▼
  data tools (rows)              render_chart(...)                    list/get_artifact_data
  agent/tools/data_tools.py      agent/tools/render_tools.py          agent/tools/artifact_tools.py
                                  builds+validates AgentUIPayload,
                                  stages it into ADK session state
                                          │
                runner reads staged payloads/artifacts from session state
                ──► { text, payloads, artifacts, context_used } ──► React renderers
```

- **`LlmAgent` (the lead agent)** — `agent/adk_agents/program_analyst/agent.py`. Brained by
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

## Plug-and-play, going forward (Phase 2+)

The ADK framework is what makes this extensible:

- **Genesis specialist assistants as tools** — `agent/tools/external_assistant_tool.py`
  (`call_cam_assistant_v2`, `call_pm_assistant_v2`, …) wraps the Genesis Assistants API so a
  sub-agent can consult a pre-built domain expert.
- **Orchestrator + `sub_agents`** — an `LlmAgent(sub_agents=[…])` routes each request to the
  right specialist (CAM, RIO/Risk, PM, RCCA), each able to fetch data, render charts, and
  consult its Genesis assistant. New agents/subagents drop in without touching the contract
  or the React layer.

This mirrors the `adk-project` orchestrator pattern; see [05-backend-and-data-tools.md](05-backend-and-data-tools.md).

← back to the [README](../README.md)
