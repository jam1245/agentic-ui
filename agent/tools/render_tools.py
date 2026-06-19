"""render_chart — the ADK function tool that drives the React UI.

This is the bridge between Google ADK (whose agents emit text + tool calls) and this
project's agent-to-UI contract. The ADK agent decides what to plot and calls `render_chart`;
the tool fetches the AUTHORITATIVE rows from a data tool (so the model never fabricates
numbers), builds + validates an `AgentUIPayload` (Contract 1), records an `ArtifactContext`
(Contract 2), and STAGES both into the ADK session state via `tool_context.state`.

After the run, `agent/runner.py` reads the staged payloads/artifacts out of session state and
returns them to React in the usual `{text, payloads, artifacts}` shape. React, the contract,
and the renderers are unchanged — ADK simply replaces the hand-rolled agent loop.
"""
from __future__ import annotations

from typing import Optional

from google.adk.tools import ToolContext
from pydantic import TypeAdapter

from ..artifacts import to_artifact_context, to_digest
from ..payloads import AgentUIPayload
from . import data_tools

_adapter: TypeAdapter[AgentUIPayload] = TypeAdapter(AgentUIPayload)

# Data tools the agent may pull authoritative rows from when rendering.
_SOURCES = {
    "get_cpi_trend": data_tools.get_cpi_trend,
    "get_spi_by_control_account": data_tools.get_spi_by_control_account,
    "get_top_risks": data_tools.get_top_risks,
    "get_program_health": data_tools.get_program_health,
    "get_cam_variance": data_tools.get_cam_variance,
}

PENDING_KEY = "pending_payloads"
ARTIFACTS_KEY = "artifacts"


def render_chart(
    component: str,
    title: str,
    source_tool: str,
    args: dict,
    fields: dict,
    summary: str,
    tool_context: ToolContext,
    user_intent: str = "",
    columns: Optional[list] = None,
    problem: str = "",
) -> dict:
    """Render a chart/table/card in the user's UI from program data.

    Call this to SHOW data visually. It pulls the real rows from the named data tool and
    renders them — you do not pass row values yourself, so the numbers are always accurate.

    Args:
        component: one of "line_chart", "bar_chart", "kpi_card", "risk_matrix", "timeline",
            "gantt", "variance_table", "fishbone", "table".
        title: short human title for the chart.
        source_tool: which data tool supplies the rows — one of get_cpi_trend,
            get_spi_by_control_account, get_top_risks, get_program_health, get_cam_variance.
        args: keyword arguments for the data tool, e.g. {"program": "P-117", "months": 6}.
        fields: mapping of data keys to roles, e.g. {"x": "month", "y": "cpi"} (line/bar),
            {"x": "likelihood", "y": "impact", "label": "risk"} (risk_matrix).
        summary: a one-sentence takeaway for the user (you author this).
        user_intent: optional — trend_analysis | comparison | distribution | status_summary |
            schedule | detail_lookup | root_cause | ranking.
        columns: optional column specs for variance_table.
        problem: optional problem statement for a fishbone.

    Returns:
        {"status": "rendered", "artifactId": ..., "rows": <n>} on success, or
        {"status": "error", "error": ...} if the data tool or payload is invalid.
    """
    fn = _SOURCES.get(source_tool)
    if fn is None:
        return {"status": "error", "error": f"Unknown source_tool '{source_tool}'. Choose one of {list(_SOURCES)}."}

    try:
        result = fn(**(args or {}))
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": f"Data tool {source_tool} failed: {exc}"}

    raw = {
        "component": component,
        "title": title,
        "userIntent": user_intent or None,
        "data": result.get("rows", []),
        "fields": fields or {},
        "metadata": {
            "source": result.get("source", "Genesis"),
            "explanation": summary,
            "filtersApplied": result.get("filters"),
        },
    }
    if columns:
        raw["columns"] = columns
    if problem:
        raw["problem"] = problem
    return _stage(raw, summary, source_tool, tool_context)


def render_structured(
    component: str,
    title: str,
    data: list,
    fields: dict,
    summary: str,
    tool_context: ToolContext,
    user_intent: str = "",
    problem: str = "",
    columns: Optional[list] = None,
) -> dict:
    """Render a chart from rows you compose yourself (qualitative / analysis-derived data).

    Use this when the content is NOT in a data tool — e.g. a fishbone (root-cause) diagram,
    a timeline of events, or a small table you assembled from analysis. For numeric program
    metrics, prefer `render_chart` (which pulls authoritative rows). Do not invent metric
    numbers here.

    Args:
        component: "fishbone", "timeline", "table", etc.
        title: short human title.
        data: the rows to display, e.g. [{"category": "People", "cause": "..."}] for fishbone.
        fields: key→role mapping if applicable.
        summary: one-sentence takeaway.
        problem: problem statement (fishbone).
        columns: column specs (table/variance_table).
    """
    raw = {
        "component": component,
        "title": title,
        "userIntent": user_intent or None,
        "data": data or [],
        "fields": fields or {},
        "metadata": {"source": "analysis", "explanation": summary},
    }
    if problem:
        raw["problem"] = problem
    if columns:
        raw["columns"] = columns
    return _stage(raw, summary, "analysis", tool_context)


def _stage(raw: dict, summary: str, source_tool: str, tool_context: ToolContext) -> dict:
    """Validate the payload (falling back to a table), record the artifact, and stage both
    into ADK session state for the runner to return to React."""
    try:
        payload = _adapter.validate_python(raw)
    except Exception:
        raw = dict(raw)
        raw["component"] = "table"
        raw.pop("columns", None)
        raw.pop("problem", None)
        payload = _adapter.validate_python(raw)

    artifact = to_artifact_context(
        payload,
        original_user_question=tool_context.state.get("last_user_message", ""),
        source_tool=source_tool,
        summary_for_future_turns=summary,
    )
    payload.artifactId = artifact.artifactId

    pending = list(tool_context.state.get(PENDING_KEY) or [])
    pending.append(payload.model_dump(exclude_none=True))
    tool_context.state[PENDING_KEY] = pending

    registry = dict(tool_context.state.get(ARTIFACTS_KEY) or {})
    registry[artifact.artifactId] = artifact.model_dump(exclude_none=True)
    tool_context.state[ARTIFACTS_KEY] = registry

    return {
        "status": "rendered",
        "artifactId": artifact.artifactId,
        "rows": len(payload.data),
        "note": "Chart is now on the user's screen. Give a one-sentence takeaway; do not re-list the data.",
    }
