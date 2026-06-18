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
    if "spi" in q or "control account" in q:
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


# Words that mean "draw me a chart" vs. "talk to me about the data already shown".
_PLOT_VERBS = ("show", "plot", "chart", "graph", "display", "visualize", "visualise", "draw", "render")
_QUESTION_MARKERS = (
    "explain", "difference", "compare", "between", " vs", "versus", "why", "what", "which",
    "how ", "highest", "lowest", "average", "mean", "biggest", "largest", "smallest", "most",
    "least", "increase", "decrease", "change", "trend", "summar", "executive", "brief",
    "leadership", "understand", "tell me", "elaborate", "describe", "interpret", "that", "this",
)

# Map question keywords to the component whose stored artifact can answer them.
_TOPIC_COMPONENT = [
    (("cpi", "cost performance", "march"), "line_chart"),
    (("spi", "schedule perf", "control account", "account"), "bar_chart"),
    (("risk", "likelihood", "impact"), "risk_matrix"),
    (("health", "kpi", "overall"), "kpi_card"),
    (("cam", "variance", "bcwp", "acwp"), "variance_table"),
]


def _wants_plot(q: str) -> bool:
    return any(v in q for v in _PLOT_VERBS)


def _is_question(question: str) -> bool:
    q = question.lower()
    return question.strip().endswith("?") or any(m in q for m in _QUESTION_MARKERS)


def _topic_component(q: str) -> Optional[str]:
    for kws, comp in _TOPIC_COMPONENT:
        if any(k in q for k in kws):
            return comp
    return None


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
# Data Q&A — the chat actually reasons over a plotted chart's rows.
# --------------------------------------------------------------------------------------

def _data_fallback(question: str, art: ArtifactContext, rows: list) -> str:
    """A DATA-GROUNDED fallback used in mock mode or when the model's prose is rejected.
    It cites real numbers from the artifact so the reply is never a content-free 'canned'
    line. Handles two common shapes: two-point comparisons and 'why did March dip'."""
    q = question.lower()
    fields = art.fields or {}
    x, y = fields.get("x"), fields.get("y")

    if x and y and rows:
        # "why did March dip?" style — name the low point.
        if "march" in q:
            mar = next((r for r in rows if str(r.get(x, "")).lower().startswith("mar")), None)
            if mar is not None:
                return (
                    f"In {art.title}, March is the low point at {mar.get(y)} before recovering "
                    f"toward target — it lines up with the late requirements baseline in the risks."
                )
        # "difference between A and B" style — find the two referenced points and subtract.
        hits = []
        for r in rows:
            label = str(r.get(x, "")).lower()
            if label and label in q and r not in hits:
                hits.append(r)
        if len(hits) >= 2:
            a, b = hits[0], hits[1]
            try:
                diff = float(b[y]) - float(a[y])
                return (
                    f"In {art.title}, {a.get(x)} {y} is {a.get(y)} and {b.get(x)} {y} is "
                    f"{b.get(y)} — a difference of {diff:+.2f}."
                )
            except (TypeError, ValueError, KeyError):
                pass
        # Otherwise lay out the series so the answer still contains the actual values.
        pts = ", ".join(f"{r.get(x)}={r.get(y)}" for r in rows[:8])
        return f"{art.title}: {pts}."

    return f"{art.title} — {art.summaryForFutureTurns}"


def _answer_about_data(client, session: GenesisSession, question: str, art: ArtifactContext) -> TurnResult:
    """Answer a free-form question using the FULL rows of a plotted chart, with the rest of
    the canvas (other artifacts) named so the model can reason across charts."""
    rows = art.fullData or []
    canvas = "; ".join(f"{d.title} ({d.artifactType})" for d in list_digests(session.state)) or "none"
    answer = _llm_prose(
        client,
        (
            "You are a program analyst talking with a user about charts already on screen.\n"
            f"Charts on the canvas: {canvas}.\n"
            f"The relevant chart is \"{art.title}\". Its full data is: {json.dumps(rows)}.\n"
            f"User question: \"{question}\"\n"
            "Answer the question directly and conversationally in 1-3 sentences, citing the "
            "exact numbers from the data. No preamble, no JSON, no reasoning out loud."
        ),
        _data_fallback(question, art, rows),
    )
    return TurnResult(answer, [], _digests(session), [{"artifactId": art.artifactId, "title": art.title}])


def _make_chart(client, session: GenesisSession, question: str, intent: ChartIntent) -> TurnResult:
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
        original_user_question=question,
        source_tool=intent.tool,
        summary_for_future_turns=summary,
    )
    payload.artifactId = artifact.artifactId
    store_artifact(session.state, artifact)
    return TurnResult(summary, [payload.model_dump(exclude_none=True)], _digests(session))


# --------------------------------------------------------------------------------------
# The turn — route between "draw a chart" and "talk about the data already drawn".
# --------------------------------------------------------------------------------------

def run_turn(client, session: GenesisSession, user_question: str) -> TurnResult:
    q = user_question.lower()
    has_art = bool(list_digests(session.state))
    wants_plot = _wants_plot(q)
    asking = _is_question(user_question)

    # A) A QUESTION about data already on the canvas → answer from the rows (don't re-plot).
    #    This is what makes the chat data-aware: "explain the difference between Jan and Jun
    #    CPI", "which control account is worst", "why did March dip" all land here.
    if has_art and asking and not wants_plot:
        comp = _topic_component(q)
        if comp:
            art = _latest(session, comp)
            if art:
                return _answer_about_data(client, session, user_question, art)
            # Topic named but not plotted yet → fall through and plot it.
        else:
            art = _latest(session)  # generic "summarize that", "tell me more"
            if art:
                return _answer_about_data(client, session, user_question, art)

    # B) A chart request → plot it (explicit "show…", or a topic not yet on the canvas).
    intent = route_chart(user_question)
    if intent and (wants_plot or _latest(session, intent.component) is None):
        return _make_chart(client, session, user_question, intent)

    # C) Topic already plotted and they referenced it without "show" → talk about it.
    if intent:
        art = _latest(session, intent.component) or _latest(session)
        if art and not wants_plot:
            return _answer_about_data(client, session, user_question, art)
        return _make_chart(client, session, user_question, intent)

    # D) Generic follow-up with no topic keyword → use the most recent chart.
    if has_art and asking:
        art = _latest(session)
        if art:
            return _answer_about_data(client, session, user_question, art)

    # E) Nothing to work with → helpful guidance (never a bare "?").
    return TurnResult(
        "I can chart CPI trend, SPI by control account, top risks, program health, or CAM "
        "variance — then discuss the numbers behind any of them. What would you like to see?",
        [], _digests(session),
    )
