"""Agent loop over the Genesis Assistants API.

Genesis (as exposed) returns text, not native tool calls — so this module gives it a small
JSON "action" protocol and runs the same reasoning loop our ADK agent does, producing the
SAME validated AgentUIPayload (Contract 1) and ArtifactContext (Contract 2). That means
the React UI and renderers are identical no matter which LLM backend you use.

Action protocol — the assistant replies with ONE JSON object per turn:
  {"action":"fetch_data","tool":"get_cpi_trend","args":{...},"then":{<render spec>}}
      → we run the data tool, build the payload from the rows + render spec, store the
        artifact, and return it for rendering. (One round trip for a typical chart.)
  {"action":"get_artifact","artifactId":"..."}     → we inject that artifact's full rows
      and ask again (drill-down / "why did March dip?").
  {"action":"render","payload":{...},"summary":"..."}  → render a payload the model built
      directly (no data tool needed).
  {"action":"reply","text":"..."}                  → plain text answer (follow-ups answered
      from context; no new visualization).

Numbers always come from the data tools, never invented by the model: for fetch_data the
model picks the tool + the *presentation* (component/fields/summary), and we attach the
real rows. This keeps the model honest about data while it drives the UI.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Callable

from . import data_tools
from .artifacts import (
    ArtifactContext,
    get_artifact,
    list_digests,
    store_artifact,
    to_artifact_context,
)
from .payloads import AgentUIPayload
from pydantic import TypeAdapter

_adapter: TypeAdapter[AgentUIPayload] = TypeAdapter(AgentUIPayload)

# Data tools the planner may choose from. Maps name -> (callable, source label).
TOOLS: dict[str, Callable[..., dict]] = {
    "get_cpi_trend": data_tools.get_cpi_trend,
    "get_spi_by_control_account": data_tools.get_spi_by_control_account,
    "get_top_risks": data_tools.get_top_risks,
    "get_program_health": data_tools.get_program_health,
    "get_cam_variance": data_tools.get_cam_variance,
}

TOOL_CATALOG = """\
get_cpi_trend(program, months)            -> monthly CPI; for trend_analysis -> line_chart
get_spi_by_control_account(program)       -> SPI per account; for comparison -> bar_chart
get_top_risks(program, limit)             -> risks w/ likelihood,impact -> risk_matrix
get_program_health(program)               -> headline metrics w/ status -> kpi_card
get_cam_variance(program, period)         -> plan vs actual by CAM -> variance_table\
"""

SYSTEM_INSTRUCTION = f"""\
You are a program-management analyst. Answer data questions by driving a UI, never by
dumping numbers as text. Reply with EXACTLY ONE JSON object (no prose, no code fences)
following this action protocol:

1) New data question -> choose a data tool AND the visualization:
   {{"action":"fetch_data","tool":"<tool>","args":{{...}},
     "then":{{"component":"line_chart|bar_chart|kpi_card|risk_matrix|variance_table|table|timeline|gantt|fishbone",
              "title":"...","userIntent":"...","fields":{{"x":"..","y":"..","label":".."}},
              "summary":"<=2 sentence takeaway","explanation":"why this component"}}}}
2) Follow-up needing the rows of a prior chart:
   {{"action":"get_artifact","artifactId":"<id from ARTIFACTS context>"}}
3) Answer a follow-up from context (no new chart):
   {{"action":"reply","text":"..."}}

Available data tools:
{TOOL_CATALOG}

Pick the component from the user's intent (trend->line_chart, compare->bar_chart,
likelihood x impact->risk_matrix, headline metrics->kpi_card, plan vs actual->variance_table).
"""


@dataclass
class GenesisSession:
    """Per-conversation state: the Genesis thread lives in the client; artifacts live here
    (mirrors ADK session state in the ADK path)."""

    state: dict[str, Any] = field(default_factory=dict)


@dataclass
class TurnResult:
    text: str
    payloads: list[dict]  # validated AgentUIPayloads (with artifactId) for the UI
    artifacts: list[dict]  # compact digests, for inspection / readables
    # Artifacts this turn pulled from prior context (e.g. "why did March dip?" rehydrated
    # the CPI chart). Lets the UI prove data is being absorbed into the conversation.
    context_used: list[dict] = field(default_factory=list)


def _extract_json(text: str) -> dict:
    """Parse the model's reply into an action object, tolerating fences / stray prose."""
    text = (text or "").strip()
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fenced:
        text = fenced.group(1).strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1:
        text = text[start : end + 1]
    return json.loads(text)


def _build_prompt(session: GenesisSession, user_question: str, injected: str = "") -> str:
    digests = list_digests(session.state)
    artifacts_block = (
        "ARTIFACTS already shown (id | title | summary):\n"
        + "\n".join(f"- {d.artifactId} | {d.title} | {d.summary}" for d in digests)
        if digests
        else "ARTIFACTS already shown: (none yet)"
    )
    return (
        f"{SYSTEM_INSTRUCTION}\n\n{artifacts_block}\n{injected}\n\nUSER QUESTION: {user_question}"
    )


def _payload_from_fetch(action: dict) -> tuple[AgentUIPayload, str, str]:
    """Run the chosen data tool and assemble a validated payload from rows + render spec."""
    tool_name = action["tool"]
    if tool_name not in TOOLS:
        raise ValueError(f"Unknown data tool: {tool_name}")
    result = TOOLS[tool_name](**(action.get("args") or {}))
    spec = action.get("then") or {}
    raw_payload = {
        "component": spec.get("component", "table"),
        "title": spec.get("title", "Results"),
        "userIntent": spec.get("userIntent"),
        "data": result.get("rows", []),
        "fields": spec.get("fields") or {},
        "metadata": {
            "source": result.get("source", "Genesis"),
            "explanation": spec.get("explanation"),
            "filtersApplied": result.get("filters"),
        },
    }
    # variance_table needs columns; fall back to table if the model omitted them.
    if raw_payload["component"] == "variance_table" and "columns" not in spec:
        raw_payload["component"] = "table"
    if "columns" in spec:
        raw_payload["columns"] = spec["columns"]
    if "problem" in spec:
        raw_payload["problem"] = spec["problem"]
    payload = _adapter.validate_python(raw_payload)
    return payload, spec.get("summary", spec.get("explanation", "")), f"{tool_name}"


def run_turn(client, session: GenesisSession, user_question: str, max_iters: int = 4) -> TurnResult:
    """Drive one user turn through Genesis, returning text + any payloads to render."""
    payloads: list[dict] = []
    context_used: list[dict] = []
    injected = ""

    for _ in range(max_iters):
        reply = client.ask(_build_prompt(session, user_question, injected))
        try:
            action = _extract_json(reply)
        except json.JSONDecodeError:
            # Not JSON -> treat as a plain text answer.
            return TurnResult(reply.strip(), payloads, _digests(session), context_used)

        kind = action.get("action")

        if kind == "fetch_data":
            payload, summary, source_tool = _payload_from_fetch(action)
            artifact = to_artifact_context(
                payload,
                original_user_question=user_question,
                source_tool=source_tool,
                summary_for_future_turns=summary,
            )
            payload.artifactId = artifact.artifactId
            store_artifact(session.state, artifact)
            payloads.append(payload.model_dump(exclude_none=True))
            return TurnResult(summary, payloads, _digests(session), context_used)

        if kind == "render":
            payload = _adapter.validate_python(action["payload"])
            artifact = to_artifact_context(
                payload,
                original_user_question=user_question,
                source_tool=payload.metadata.source,
                summary_for_future_turns=action.get("summary", payload.metadata.explanation or ""),
            )
            payload.artifactId = artifact.artifactId
            store_artifact(session.state, artifact)
            payloads.append(payload.model_dump(exclude_none=True))
            return TurnResult(action.get("summary", ""), payloads, _digests(session), context_used)

        if kind == "get_artifact":
            art = _resolve_artifact(session, action.get("artifactId", ""))
            rows = art.fullData if art else []
            if art:
                # Record that this turn drew on prior context (for the UI's "absorbed" badge).
                context_used.append({"artifactId": art.artifactId, "title": art.title})
            injected = f"\nROWS FOR ARTIFACT {action.get('artifactId')}:\n{json.dumps(rows)[:4000]}"
            continue  # loop again with the rehydrated rows in context

        if kind == "reply":
            return TurnResult(action.get("text", ""), payloads, _digests(session), context_used)

        # Unknown action -> stop defensively.
        return TurnResult(reply.strip(), payloads, _digests(session), context_used)

    return TurnResult("(stopped: too many steps)", payloads, _digests(session), context_used)


def _resolve_artifact(session: GenesisSession, artifact_id: str) -> ArtifactContext | None:
    if artifact_id == "__latest_line_chart__":
        for d in reversed(list_digests(session.state)):
            if d.artifactType == "line_chart":
                return get_artifact(session.state, d.artifactId)
    return get_artifact(session.state, artifact_id)


def _digests(session: GenesisSession) -> list[dict]:
    return [d.model_dump(exclude_none=True) for d in list_digests(session.state)]
