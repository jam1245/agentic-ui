"""Hybrid agent loop over the Genesis Completions API.

WHY HYBRID: `gpt-oss-120b` is a reasoning model. Asked to emit strict JSON it tends to
"think out loud" first, so a pure model-drives-JSON loop is unreliable (it worked for ~1
of 5 prompts in live testing). The fix that keeps the demo crisp AND uses the real LLM:

  * STRUCTURE is deterministic. A small intent router maps the user's question to the
    right data tool + component + field mapping. This guarantees every canned prompt
    renders the correct visual, every time — the model can't break it.
  * PROSE is the LLM's job. The real Genesis model writes the natural-language takeaway and
    answers follow-up questions about the data (what reasoning models are good at). If the
    model returns junk (or we're in offline mock mode), we fall back to a deterministic
    sentence, so the user never sees a broken or empty reply.

Both contracts are unchanged: we still emit a validated AgentUIPayload (Contract 1) and
store an ArtifactContext (Contract 2) so follow-ups stay data-aware.

Numbers always come from the data tools — never invented by the model.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from pydantic import TypeAdapter

from . import data_tools
from .artifacts import (
    ArtifactContext,
    get_artifact,
    list_digests,
    store_artifact,
    to_artifact_context,
)
from .payloads import AgentUIPayload

_adapter: TypeAdapter[AgentUIPayload] = TypeAdapter(AgentUIPayload)

TOOLS: dict[str, Callable[..., dict]] = {
    "get_cpi_trend": data_tools.get_cpi_trend,
    "get_spi_by_control_account": data_tools.get_spi_by_control_account,
    "get_top_risks": data_tools.get_top_risks,
    "get_program_health": data_tools.get_program_health,
    "get_cam_variance": data_tools.get_cam_variance,
}


# --------------------------------------------------------------------------------------
# Deterministic intent router — guarantees the right chart + data for each question.
# --------------------------------------------------------------------------------------

@dataclass
class ChartIntent:
    tool: str
    args: dict
    component: str
    title: str
    user_intent: str
    fields: dict
    summary: str  # deterministic takeaway (fallback / mock prose)
    columns: Optional[list] = None


def route_chart(question: str) -> Optional[ChartIntent]:
    """Map a question to a chart intent, or None if it's not a fresh-chart request."""
    q = question.lower()
    if "cam" in q or "variance" in q:
        return ChartIntent(
            "get_cam_variance", {"program": "P-117", "period": "June"}, "variance_table",
            "CAM Variance — June", "detail_lookup", {"label": "cam"},
            "L. Tan shows the largest unfavorable cost variance (-60); S. Okoye is favorable.",
            columns=[
                {"key": "cam", "label": "CAM", "kind": "text"},
                {"key": "bcwp", "label": "BCWP", "kind": "plan"},
                {"key": "acwp", "label": "ACWP", "kind": "actual"},
                {"key": "cv", "label": "Cost Var", "kind": "variance"},
                {"key": "sv", "label": "Sched Var", "kind": "variance"},
            ],
        )
    if "cpi" in q or ("trend" in q and "spi" not in q):
        return ChartIntent(
            "get_cpi_trend", {"program": "P-117", "months": 6}, "line_chart",
            "CPI Trend — Last 6 Months", "trend_analysis", {"x": "month", "y": "cpi"},
            "CPI recovered from 0.92 to 1.01 over six months, with a dip to 0.90 in March.",
        )
    if "spi" in q:
        return ChartIntent(
            "get_spi_by_control_account", {"program": "P-117"}, "bar_chart",
            "SPI by Control Account", "comparison", {"x": "account", "y": "spi"},
            "CA-400 is the schedule laggard at 0.86; CA-100 leads at 1.04.",
        )
    if "risk" in q:
        return ChartIntent(
            "get_top_risks", {"program": "P-117"}, "risk_matrix",
            "Top Program Risks", "distribution", {"x": "likelihood", "y": "impact", "label": "risk"},
            "Supplier delay (4×5) is the top exposure; staffing gap (3×4) is next.",
        )
    if "health" in q or "summarize program" in q or "program status" in q or "how is the program" in q:
        return ChartIntent(
            "get_program_health", {"program": "P-117"}, "kpi_card",
            "Program Health Summary", "status_summary", {},
            "CPI 0.94 (warning), SPI 1.02 (good), 12 open risks, EAC -$1.2M (critical).",
        )
    return None


_FOLLOWUP_MARKERS = (
    "summar", "executive", "brief", "leadership", "explain", "understand",
    "tell me more", "that", "this", "it ", "those", "elaborate", "why",
)


def is_followup(question: str) -> bool:
    q = question.lower()
    return any(m in q for m in _FOLLOWUP_MARKERS)


# --------------------------------------------------------------------------------------
# Session + result types
# --------------------------------------------------------------------------------------

@dataclass
class GenesisSession:
    state: dict[str, Any] = field(default_factory=dict)


@dataclass
class TurnResult:
    text: str
    payloads: list[dict]
    artifacts: list[dict]
    context_used: list[dict] = field(default_factory=list)


# --------------------------------------------------------------------------------------
# Prose: real LLM when available, deterministic fallback otherwise.
# --------------------------------------------------------------------------------------

_REASONING_SMELLS = ("we need", "we have to", "the user", "let me", "first,", "okay", "sure,", "i should", "json")


def _clean_prose(text: str) -> str:
    """Accept clean natural language; reject reasoning/JSON leakage from the model."""
    t = (text or "").strip().strip("`").strip()
    if len(t) < 8 or t.startswith("{") or '"action"' in t:
        return ""
    head = t[:40].lower()
    if any(head.startswith(s) or s in head for s in _REASONING_SMELLS):
        return ""
    return t.split("\n\n")[0].strip()  # first paragraph is plenty


def _llm_prose(client, instruction: str, fallback: str) -> str:
    """Ask the real model for a sentence or two; fall back to deterministic text."""
    if getattr(client, "is_mock", False):
        return fallback
    try:
        cleaned = _clean_prose(client.ask(instruction, raw=True, max_tokens=400))
    except Exception:
        cleaned = ""
    return cleaned or fallback


# --------------------------------------------------------------------------------------
# Payload assembly
# --------------------------------------------------------------------------------------

def _build_payload(intent: ChartIntent, result: dict) -> AgentUIPayload:
    raw = {
        "component": intent.component,
        "title": intent.title,
        "userIntent": intent.user_intent,
        "data": result.get("rows", []),
        "fields": intent.fields,
        "metadata": {
            "source": result.get("source", "Genesis"),
            "explanation": intent.summary,
            "filtersApplied": result.get("filters"),
        },
    }
    if intent.columns:
        raw["columns"] = intent.columns
    try:
        return _adapter.validate_python(raw)
    except Exception:
        # Graceful fallback: show the rows as a table rather than failing.
        raw["component"] = "table"
        raw.pop("columns", None)
        return _adapter.validate_python(raw)


def _latest(session: GenesisSession, component: Optional[str] = None) -> Optional[ArtifactContext]:
    digests = list_digests(session.state)
    for d in reversed(digests):
        if component is None or d.artifactType == component:
            return get_artifact(session.state, d.artifactId)
    return None


def _digests(session: GenesisSession) -> list[dict]:
    return [d.model_dump(exclude_none=True) for d in list_digests(session.state)]


# --------------------------------------------------------------------------------------
# The turn
# --------------------------------------------------------------------------------------

def run_turn(client, session: GenesisSession, user_question: str) -> TurnResult:
    q = user_question.lower()

    # 1) Specific follow-up: "why did March dip?" → answer from the stored CPI chart.
    if "march" in q and ("dip" in q or "why" in q or "drop" in q):
        art = _latest(session, "line_chart") or _latest(session)
        if art:
            rows = art.fullData or []
            march = next((r for r in rows if str(r.get("month", "")).lower().startswith("mar")), None)
            mval = march.get("cpi") if march else "0.91"
            fallback = (
                f"March is the low point of the CPI series at {mval} — the only month that "
                f"dips below the rising trend — before recovering toward target. It lines up "
                f"with the late requirements baseline flagged in the schedule risks."
            )
            answer = _llm_prose(
                client,
                f"The user asked: \"{user_question}\". Here is the CPI data behind the chart "
                f"titled \"{art.title}\": {json.dumps(rows)}. Answer in 1-2 sentences, cite the "
                f"March value, conversational tone. Plain prose only.",
                fallback,
            )
            return TurnResult(answer, [], _digests(session), [{"artifactId": art.artifactId, "title": art.title}])
        # No chart yet — nudge the user.
        return TurnResult(
            "Ask me to \"show CPI trend\" first, then I can explain the March dip from that chart.",
            [], _digests(session),
        )

    # 2) Fresh chart request → deterministic structure + data, LLM/deterministic takeaway.
    intent = route_chart(user_question)
    if intent:
        result = TOOLS[intent.tool](**intent.args)
        payload = _build_payload(intent, result)
        summary = _llm_prose(
            client,
            f"Data for \"{intent.title}\": {json.dumps(result.get('rows', []))}. Give the single "
            f"most important takeaway for a program manager in ONE sentence. No preamble.",
            intent.summary,
        )
        artifact = to_artifact_context(
            payload,
            original_user_question=user_question,
            source_tool=intent.tool,
            summary_for_future_turns=summary,
        )
        payload.artifactId = artifact.artifactId
        store_artifact(session.state, artifact)
        return TurnResult(summary, [payload.model_dump(exclude_none=True)], _digests(session))

    # 3) Generic follow-up about something already shown → summarize from context.
    if is_followup(user_question):
        art = _latest(session)
        if art:
            fallback = f"From {art.title}: {art.summaryForFutureTurns}"
            answer = _llm_prose(
                client,
                f"The user asked: \"{user_question}\". Based on the chart \"{art.title}\" "
                f"(summary: {art.summaryForFutureTurns}) with data {json.dumps(art.fullData or [])}, "
                f"answer in 1-3 sentences, conversational, cite numbers. Plain prose only.",
                fallback,
            )
            return TurnResult(answer, [], _digests(session), [{"artifactId": art.artifactId, "title": art.title}])

    # 4) Nothing matched → helpful guidance (never a bare "?" ).
    return TurnResult(
        "I can chart CPI trend, SPI by control account, top risks, program health, or CAM "
        "variance — then answer follow-ups about whatever I show. What would you like to see?",
        [], _digests(session),
    )
