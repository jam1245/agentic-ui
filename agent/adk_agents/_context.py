"""Canvas awareness — inject what's on screen into the agent's context every turn.

ADK lets an agent's `instruction` be a provider `(ReadonlyContext) -> str`. We use that to
append a compact, always-fresh summary of every chart/card currently rendered (its title,
type, takeaway, field schema, row count, and a one-row sample) — read from the artifact
registry in session state. So the LLM ALWAYS knows the whole canvas without having to ask,
and can decide which charts to deep-dive (via get_artifact_data) and connect across them.

This keeps full datasets OUT of the prompt (cheap) while guaranteeing awareness.
"""
from __future__ import annotations

import json
from typing import Callable

from google.adk.agents.readonly_context import ReadonlyContext

ARTIFACTS_KEY = "artifacts"
_MAX_ARTIFACTS = 10
_SUMMARY_CAP = 160


def _canvas_block(state) -> str:
    registry = (state.get(ARTIFACTS_KEY) if state else None) or {}
    items = list(registry.values())[-_MAX_ARTIFACTS:]
    if not items:
        return "CHARTS ON SCREEN: none yet — render one when the user asks to see data."

    lines = []
    for a in items:
        fields = a.get("fields") or {}
        fstr = ", ".join(f"{k}={v}" for k, v in fields.items()) or "—"
        rows = a.get("fullData") or a.get("dataSample") or []
        sample = json.dumps(rows[:1])[:200] if rows else "[]"
        summary = (a.get("summaryForFutureTurns") or "")[:_SUMMARY_CAP]
        lines.append(
            f'- [{a.get("artifactId")}] "{a.get("title")}" ({a.get("artifactType")}) — '
            f"{summary} | fields: {fstr} | rows: {len(rows)} | sample: {sample}"
        )

    return (
        "CHARTS CURRENTLY ON SCREEN (the user can see these):\n"
        + "\n".join(lines)
        + "\n\nWhen the user asks a question, reason across these charts. Call "
        "get_artifact_data(artifactId) to pull the full rows of any chart you need detail on, "
        "and make connections BETWEEN charts where relevant (e.g., relate a cost trend to a "
        "risk, or a schedule slip to program health). Cite real numbers; never invent them."
    )


def with_canvas(base_instruction: str) -> Callable[[ReadonlyContext], str]:
    """Wrap a static instruction so the live canvas summary is appended every turn."""

    def provider(ctx: ReadonlyContext) -> str:
        return f"{base_instruction}\n\n---\n{_canvas_block(ctx.state)}"

    return provider
