"""UI-layer ADK tools — the bridge from data to rendering AND to conversational memory.

`render_ui` does TWO things now, satisfying both contracts:
  1. Returns the AgentUIPayload so the front end renders the component.
  2. Normalizes it into an ArtifactContext and stores it in session state so the main
     chat agent can answer follow-ups about it later.

`list_artifacts` and `get_artifact_data` let the agent recall what it has shown and
rehydrate full rows on demand — without keeping every dataset in the standing prompt.

Why a tool and not "the agent draws the chart": the agent stays a reasoning engine; the
contract is enforced at the boundary; the UI advertises exactly which components exist.
"""
from __future__ import annotations

from typing import Any

from google.adk.tools import ToolContext
from pydantic import TypeAdapter

from .artifacts import get_artifact, list_digests, store_artifact, to_artifact_context
from .payloads import AgentUIPayload

_adapter: TypeAdapter[AgentUIPayload] = TypeAdapter(AgentUIPayload)

# The allow-list the agent is told about (mirrors src/components/registry.ts).
SUPPORTED_COMPONENTS = [
    "table",
    "line_chart",
    "bar_chart",
    "kpi_card",
    "risk_matrix",
    "timeline",
    "gantt",
    "variance_table",
    "fishbone",
]


def render_ui(
    payload: dict[str, Any],
    original_user_question: str,
    summary_for_future_turns: str,
    tool_context: ToolContext,
    source_tool: str = "",
) -> dict[str, Any]:
    """Render a rich UI component for the user and register it as a conversational artifact.

    Call this INSTEAD of replying with a table in text whenever the answer is data.

    Args:
        payload: An AgentUIPayload (component, title, data, fields, metadata).
            component: table | line_chart | bar_chart | kpi_card | risk_matrix |
                       timeline | gantt | variance_table | fishbone
            data: list of row objects; fields: { x, y, groupBy, value, label };
            metadata: { source, explanation, filtersApplied }.
        original_user_question: The user's question that produced this artifact. Stored so
            later turns can resolve references like "this chart" / "that".
        summary_for_future_turns: A 1-2 sentence takeaway (e.g. "CPI improved from 0.92 to
            1.01 with a dip in March"). This is injected into future prompts — make it
            self-contained.
        source_tool: The data tool that produced the rows, e.g. "evms_mcp.get_cpi_history".

    Returns:
        The validated payload (echoed for rendering) plus the artifactId. Do NOT also
        describe the full data in text — the component shows it and the artifact stores it.
    """
    # Validate at the boundary; on failure ADK feeds the error back so the agent retries.
    validated = _adapter.validate_python(payload)

    # SECOND CONTRACT: build + persist the artifact context in session state.
    artifact = to_artifact_context(
        validated,
        original_user_question=original_user_question,
        source_tool=source_tool or validated.metadata.source,
        summary_for_future_turns=summary_for_future_turns,
    )
    # Reflect the (possibly generated) id back onto the payload so UI + context share it.
    rendered = validated.model_dump(exclude_none=True)
    rendered["artifactId"] = artifact.artifactId
    store_artifact(tool_context.state, artifact)

    return {"rendered": True, "artifactId": artifact.artifactId, "payload": rendered}


def list_artifacts(tool_context: ToolContext) -> dict[str, Any]:
    """List compact summaries of every artifact rendered so far this conversation.

    Use this to recall what charts/tables/cards you have already shown the user, so you can
    answer follow-ups like "summarize that" or "compare this to SPI".
    """
    return {"artifacts": [d.model_dump(exclude_none=True) for d in list_digests(tool_context.state)]}


def get_artifact_data(artifact_id: str, tool_context: ToolContext) -> dict[str, Any]:
    """Retrieve the full underlying data for a previously rendered artifact.

    Call this only when a follow-up needs row-level detail not in the summary (e.g. "why
    did March dip?" → fetch the CPI rows → inspect March). If the rows are not cached, use
    the returned dataRef to re-query the original source tool instead.
    """
    artifact = get_artifact(tool_context.state, artifact_id)
    if not artifact:
        return {"error": f"No artifact with id {artifact_id}"}
    return {
        "artifactId": artifact_id,
        "title": artifact.title,
        "fields": artifact.fields,
        "filtersApplied": artifact.filtersApplied,
        "data": artifact.fullData or artifact.dataSample or [],
        "dataRef": artifact.dataRef,
    }
