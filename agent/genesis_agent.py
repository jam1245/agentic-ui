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
import os
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from pydantic import TypeAdapter

from .tools import data_tools
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
# Answering questions about the data.
#
# DESIGN: let the LLM actually CONVERSE — handle open-ended asks ("generate a plan",
# "summarize for a director", "what should I worry about") with real insight. We give it a
# rich data brief (the chart's rows + computed key facts + the canvas inventory) and call
# the CHAT endpoint, which returns the model's FINAL answer rather than its chain-of-thought
# (the source of the earlier junk). We extract/clean defensively; if the model still returns
# something unusable (or we're offline/forced), we fall back to a deterministic, data-
# grounded answer from `_analyze`. So: the LLM shines when it can, and the reply is never
# broken or content-free.
# --------------------------------------------------------------------------------------

# Smells that mean the model leaked its reasoning instead of an answer → reject, fall back.
_REASON_SMELL = (
    "<|", "```", "we need to", "we have to", "the user wants", "the answer should",
    "the answer must", "let me think", "i should", "analysis", "channel",
)


def _extract_final(text: str) -> str:
    """Pull the model's final answer out of reasoning-model output (harmony channels, etc.)."""
    t = text or ""
    for marker in ("<|channel|>final<|message|>", "assistantfinal", "final<|message|>", "<|message|>"):
        if marker in t:
            t = t.split(marker)[-1]
    t = re.sub(r"<\|[^|]*\|>", " ", t)        # strip any remaining harmony tokens
    return t.strip().strip('"').strip()


def _usable(text: str) -> bool:
    """Accept multi-sentence conversational answers; reject leaked reasoning/markup."""
    t = (text or "").strip()
    if len(t) < 15:
        return False
    low = t.lower()
    return not any(s in low for s in _REASON_SMELL)


def _converse(client, session: GenesisSession, question: str, art: ArtifactContext) -> Optional[str]:
    """Let the real LLM answer conversationally with the chart's data in context. Returns
    None to signal 'use the deterministic fallback' (mock, disabled, or unusable output)."""
    if getattr(client, "is_mock", False) or os.getenv("GENESIS_NO_LLM") == "1":
        return None
    rows = art.fullData or []
    canvas = ", ".join(d.title for d in list_digests(session.state)) or "none"
    system = (
        "You are a seasoned program-management analyst talking with a program team about charts "
        "already on their screen. Answer in 2-5 sentences of plain prose: cite the actual numbers, "
        "explain what they mean for the program, and give practical, actionable guidance. Do not "
        "show your reasoning, no markdown headers, no bullet lists unless explicitly asked."
    )
    user = (
        f"Charts on screen: {canvas}.\n"
        f'Focus chart: "{art.title}".\n'
        f"Data rows: {json.dumps(rows)}\n"
        f"Key facts (computed, authoritative): {_key_facts(art, rows)}\n\n"
        f"Question: {question}"
    )
    try:
        raw = client.converse(system, user, max_tokens=600)
    except Exception:
        return None
    answer = _extract_final(raw)
    return answer if _usable(answer) else None


def _num(v) -> Optional[float]:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _key_facts(art: ArtifactContext, rows: list) -> str:
    """A compact, CORRECT summary of the rows (min/max/avg/trend or scores) handed to the LLM
    alongside the raw data so it grounds its answer in real numbers instead of guessing."""
    fields = art.fields or {}
    x, y, label = fields.get("x"), fields.get("y"), fields.get("label")
    if x and y and label and rows:  # risk matrix
        scored = sorted(
            ((str(r.get(label)), (_num(r.get(x)) or 0) * (_num(r.get(y)) or 0)) for r in rows),
            key=lambda s: -s[1],
        )
        return "likelihood×impact scores: " + ", ".join(f"{n}={s:g}" for n, s in scored)
    if x and y and rows and any(_num(r.get(y)) is not None for r in rows):
        pts = [(str(r.get(x)), _num(r.get(y))) for r in rows if _num(r.get(y)) is not None]
        lo, hi = min(pts, key=lambda p: p[1]), max(pts, key=lambda p: p[1])
        avg = sum(v for _, v in pts) / len(pts)
        return (
            f"min {lo[1]:g} ({lo[0]}), max {hi[1]:g} ({hi[0]}), avg {avg:.2f}, "
            f"first {pts[0][1]:g} ({pts[0][0]}), last {pts[-1][1]:g} ({pts[-1][0]})"
        )
    if rows and "label" in rows[0] and "value" in rows[0]:
        return ", ".join(f"{r.get('label')}={r.get('value')}" for r in rows)
    if rows:
        return "; ".join(", ".join(f"{k}={r.get(k)}" for k in rows[0]) for r in rows[:6])
    return art.summaryForFutureTurns


def _analyze(question: str, art: ArtifactContext, rows: list) -> str:
    """Compute a correct, data-grounded answer from an artifact's rows. Handles the common
    analytical questions per chart type; falls back to laying out the actual values."""
    q = question.lower()
    fields = art.fields or {}
    x, y, label = fields.get("x"), fields.get("y"), fields.get("label")
    title = art.title

    # Risk matrix: rank by likelihood × impact.
    if x and y and label and rows:
        scored = [
            (str(r.get(label)), _num(r.get(x)) or 0, _num(r.get(y)) or 0, (_num(r.get(x)) or 0) * (_num(r.get(y)) or 0))
            for r in rows
        ]
        scored = [s for s in scored if s[0]]
        if scored:
            band = lambda sc: "high" if sc >= 15 else "moderate" if sc >= 8 else "low"
            # A specific risk named in the question → describe just that one.
            for name, lk, im, sc in scored:
                if name.lower() in q:
                    return (
                        f'In {title}, "{name}" has likelihood {lk:g} and impact {im:g} '
                        f"(score {sc:g}) — a {band(sc)} exposure."
                    )
            ranked = sorted(scored, key=lambda s: -s[3])
            if any(w in q for w in ("brief", "leadership", "important", "prioriti", "focus", "worst", "highest", "top", "biggest", "less")):
                top, low = ranked[0], ranked[-1]
                rest = "; ".join(f"{n} ({sc:g})" for n, _lk, _im, sc in ranked)
                return (
                    f'Brief leadership on "{top[0]}" (likelihood×impact {top[3]:g}) first; '
                    f'"{low[0]}" ({low[3]:g}) is the least pressing. Full ranking: {rest}.'
                )
            listing = "; ".join(f"{n} ({sc:g})" for n, _lk, _im, sc in ranked)
            return f"{title} ranked by likelihood×impact: {listing}."

    # XY series (line / bar charts).
    if x and y and rows and any(_num(r.get(y)) is not None for r in rows):
        pts = [(str(r.get(x)), _num(r.get(y))) for r in rows if _num(r.get(y)) is not None]
        hits = [(l, v) for (l, v) in pts if l.lower() in q]
        if any(w in q for w in ("differ", "compare", "between", " vs", "versus")) and len(hits) >= 2:
            (la, va), (lb, vb) = hits[0], hits[1]
            return f"In {title}, {la} {y} is {va:g} and {lb} {y} is {vb:g} — a difference of {vb - va:+.2f}."
        if len(hits) == 1 and any(w in q for w in ("value", "what", "how much", "level", "is the", "in ")):
            la, va = hits[0]
            return f"In {title}, {la} {y} is {va:g}."
        if any(w in q for w in ("highest", "max", "peak", "best", "top", "most", "largest", "greatest")):
            l, v = max(pts, key=lambda p: p[1])
            return f"The highest {y} in {title} is {v:g} ({l})."
        if any(w in q for w in ("lowest", "min", "worst", "smallest", "least", "dip", "drop", "low point")):
            l, v = min(pts, key=lambda p: p[1])
            extra = " It lines up with the late requirements baseline in the risks." if l.lower().startswith("mar") else ""
            return f"The lowest {y} in {title} is {v:g} ({l}).{extra}"
        if any(w in q for w in ("average", "mean", "typical")):
            avg = sum(v for _, v in pts) / len(pts)
            return f"The average {y} in {title} is {avg:.2f} across {len(pts)} points."
        if any(w in q for w in ("trend", "change", "overall", "direction", "improv", "declin", "start", "end")):
            (l0, v0), (l1, v1) = pts[0], pts[-1]
            d = v1 - v0
            word = "rose" if d > 0 else "fell" if d < 0 else "held steady"
            return f"In {title}, {y} {word} from {v0:g} ({l0}) to {v1:g} ({l1}) — a change of {d:+.2f}."
        series = ", ".join(f"{l}={v:g}" for l, v in pts[:8])
        return f"{title}: {series}."

    # KPI cards (label / value rows).
    if rows and "label" in rows[0] and "value" in rows[0]:
        for r in rows:
            if str(r.get("label", "")).lower() in q:
                status = f" ({r['status']})" if r.get("status") else ""
                return f"In {title}, {r['label']} is {r['value']}{status}."
        items = ", ".join(f"{r.get('label')}: {r.get('value')}" for r in rows)
        return f"{title} — {items}."

    # Variance table (cost/schedule variance rows).
    if rows and "cv" in rows[0]:
        lab = label or "cam"
        if any(w in q for w in ("worst", "largest", "biggest", "overrun", "problem", "attention")):
            worst = min(rows, key=lambda r: _num(r.get("cv")) or 0)
            return f"In {title}, {worst.get(lab)} has the largest unfavorable cost variance (CV {worst.get('cv')})."
        listing = "; ".join(f"{r.get(lab)}: CV {r.get('cv')}, SV {r.get('sv')}" for r in rows)
        return f"{title} — {listing}."

    # Anything else: lay out the rows so the answer still contains real values.
    if rows:
        keys = list(rows[0].keys())
        body = "; ".join(", ".join(f"{k}={r.get(k)}" for k in keys) for r in rows[:5])
        return f"{title} — {body}."
    return f"{title} — {art.summaryForFutureTurns}"


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

def _answer_about_data(client, session: GenesisSession, question: str, art: ArtifactContext) -> TurnResult:
    """Answer a question about a plotted chart. The LLM converses with the data in context
    (so it can plan, summarize for a director, judge what's concerning); if its output is
    unusable — or we're offline — we fall back to a deterministic, data-grounded answer."""
    rows = art.fullData or []
    answer = _converse(client, session, question, art) or _analyze(question, art, rows)
    return TurnResult(
        answer, [], _digests(session),
        [{"artifactId": art.artifactId, "title": art.title}],
    )


def _make_chart(client, session: GenesisSession, question: str, intent: ChartIntent) -> TurnResult:
    result = TOOLS[intent.tool](**intent.args)
    payload = _build_payload(intent, result)
    # The chart itself carries the detail; a deterministic one-line takeaway is reliable.
    summary = intent.summary
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
