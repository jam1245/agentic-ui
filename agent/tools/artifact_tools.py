"""Artifact-recall tools — let the agent answer follow-ups about charts it already rendered.

These read the per-conversation artifact registry stored in ADK session state by
render_chart. `get_artifact_data` rehydrates a chart's full rows so the agent can reason
over them ("why did March dip?", "which control account is worst?") instead of re-plotting.
Calling it also records `context_used`, which the UI surfaces as the "🧠 used context" badge.
"""
from __future__ import annotations

from google.adk.tools import ToolContext

ARTIFACTS_KEY = "artifacts"
CONTEXT_USED_KEY = "context_used"


def list_artifacts(tool_context: ToolContext) -> dict:
    """List the charts already shown this conversation (id, title, summary) so you can
    decide which one a follow-up question refers to."""
    registry = tool_context.state.get(ARTIFACTS_KEY) or {}
    items = [
        {"artifactId": a.get("artifactId"), "title": a.get("title"),
         "summary": a.get("summaryForFutureTurns"), "type": a.get("artifactType")}
        for a in registry.values()
    ]
    return {"artifacts": items}


def get_artifact_data(artifact_id: str, tool_context: ToolContext) -> dict:
    """Get the full underlying rows of a previously rendered chart so you can answer a
    question about it with exact numbers. Use the artifactId from list_artifacts.

    Args:
        artifact_id: the id of the chart to inspect.
    """
    registry = tool_context.state.get(ARTIFACTS_KEY) or {}
    art = registry.get(artifact_id)
    if not art:
        return {"status": "error", "error": f"No artifact {artifact_id}. Call list_artifacts first."}

    used = list(tool_context.state.get(CONTEXT_USED_KEY) or [])
    if not any(u.get("artifactId") == artifact_id for u in used):
        used.append({"artifactId": artifact_id, "title": art.get("title")})
    tool_context.state[CONTEXT_USED_KEY] = used

    return {
        "status": "ok",
        "title": art.get("title"),
        "fields": art.get("fields"),
        "filtersApplied": art.get("filtersApplied"),
        "data": art.get("fullData") or art.get("dataSample") or [],
    }
