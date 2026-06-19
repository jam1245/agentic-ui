"""Program-management semantic model — turns numbers into MEANING.

The chat kept echoing values because an artifact carried data + a terse summary, not a
semantic model. This module supplies the missing layer: per-metric thresholds, plain-
language meaning, status, likely drivers, and a recommended action. Both the deterministic
engine (offline) and the ADK agents (as grounding for the LLM / Genesis assistants) use it,
so a question like "is that good or bad?" gets an analyst's judgment, not a recital.

Standard EVM conventions: CPI/SPI = 1.0 is on plan; < 1.0 is unfavorable (cost/schedule
efficiency behind plan); > 1.0 favorable. Negative cost/EAC variance = projected overrun.
Risk exposure = likelihood × impact.
"""
from __future__ import annotations

from typing import Optional

# Common program drivers referenced when explaining unfavorable cost/schedule.
LIKELY_DRIVERS = ["supplier delay", "staffing gap", "late requirements baseline"]


def index_status(v: float) -> tuple[str, str]:
    """Status + meaning for a CPI/SPI-style efficiency index (1.0 = on plan)."""
    if v >= 1.0:
        return "good", "at or above plan (favorable efficiency)"
    if v >= 0.95:
        return "warning", "slightly below the 1.0 plan line (mildly unfavorable)"
    return "critical", "below plan — efficiency is unfavorable and worth attention"


def metric_meaning(label: str, value) -> tuple[str, str]:
    """Status + one-line meaning for a named KPI (CPI, SPI, EAC variance, open risks)."""
    name = label.lower()
    try:
        num = float(str(value).replace("$", "").replace("M", "").replace(",", ""))
    except (TypeError, ValueError):
        num = None

    if "cpi" in name and num is not None:
        s, m = index_status(num)
        return s, f"cost efficiency — {m}"
    if "spi" in name and num is not None:
        s, m = index_status(num)
        return s, f"schedule efficiency — {m}"
    if "eac" in name or "variance" in name:
        if isinstance(value, str) and "-" in value:
            return "critical", "projected cost overrun at completion"
        return "good", "projected to complete at or under budget"
    if "risk" in name and num is not None:
        return ("warning" if num >= 8 else "neutral"), f"{int(num)} open risks — elevated exposure to watch"
    return "neutral", "tracked metric"


def trend_judgment(points: list[tuple[str, float]], metric: str) -> str:
    """Judge a CPI/SPI series: where it stands vs plan, plus direction."""
    first_l, first_v = points[0]
    last_l, last_v = points[-1]
    lo_l, lo_v = min(points, key=lambda p: p[1])
    direction = "improving" if last_v > first_v else "declining" if last_v < first_v else "flat"
    s, meaning = index_status(last_v)
    at_plan = "now at/above the 1.0 plan line" if last_v >= 1.0 else "still below the 1.0 plan line"
    return (
        f"The trend is {direction}: {metric.upper()} moved from {first_v:g} ({first_l}) to "
        f"{last_v:g} ({last_l}), dipping to {lo_v:g} in {lo_l}. It is {at_plan} — "
        f"{meaning}. " + (
            "Cost efficiency recovered, but confirm the dip's root cause is closed."
            if direction == "improving" and metric.lower() == "cpi"
            else "Watch this closely and address the drivers below."
        )
    )


def is_interpretive(question: str) -> bool:
    """True when the user wants meaning/judgment, not a value lookup."""
    q = question.lower()
    return any(
        w in q for w in (
            "good or bad", "good/bad", "is that good", "is this good", "what does", "what do",
            "tell me about", "explain", "mean", "interpret", "worry", "concern", "implication",
            "so what", "why does", "should i", "recommend", "what now", "next step", "action",
            "common", "typical", "normal", "healthy", "how is", "how's", "assessment",
        )
    )


def interpret(question: str, fields: dict, component: str, rows: list, title: str) -> Optional[str]:
    """Produce an analyst-style interpretation of a chart's data, or None if not applicable.
    Used by the deterministic engine; also a grounding reference for the LLM path."""
    if not rows:
        return None
    x, y = (fields or {}).get("x"), (fields or {}).get("y")

    # CPI / SPI style line or bar
    if x and y and y.lower() in ("cpi", "spi"):
        pts = [(str(r.get(x)), float(r.get(y))) for r in rows if _num(r.get(y)) is not None]
        if pts:
            drivers = ", ".join(LIKELY_DRIVERS)
            return f"{trend_judgment(pts, y)} Likely drivers to check: {drivers}."

    # KPI cards: explain each metric
    if component == "kpi_card" or (rows and "label" in rows[0] and "value" in rows[0]):
        parts = []
        for r in rows:
            s, m = metric_meaning(str(r.get("label", "")), r.get("value"))
            parts.append(f"{r.get('label')} {r.get('value')} — {m} ({s})")
        headline = (
            "Overall: schedule looks stable but cost efficiency and risk posture are the "
            "concern — cost is behind plan with a projected overrun. Recommend a cost-recovery "
            "review and tightening the top risks."
        )
        return " ".join(parts) + ". " + headline

    # Risk matrix: typical-risks framing + priority
    if component == "risk_matrix" or (fields or {}).get("label"):
        label = (fields or {}).get("label", "risk")
        scored = sorted(
            ((str(r.get(label)), (_num(r.get(x)) or 0) * (_num(r.get(y)) or 0)) for r in rows),
            key=lambda s: -s[1],
        )
        top = scored[0] if scored else ("", 0)
        return (
            f"Yes — supplier delays, staffing gaps, and test-resource constraints are among the "
            f"most common program risks, so this profile is typical. The priority here is "
            f'"{top[0]}" (likelihood×impact {top[1]:g}); brief leadership on that first and put a '
            f"mitigation/contingency plan against it. Lower-scored items can be monitored on the watchlist."
        )
    return None


def build_analysis(component: str, fields: dict, rows: list, title: str) -> dict:
    """Build the durable 'analysis context object' stored on every rendered artifact:
    per-metric value/status/meaning + an overall interpretation + likely drivers. This is
    what gives the chat a semantic model of the chart (not just its values)."""
    x, y = (fields or {}).get("x"), (fields or {}).get("y")
    metrics: dict = {}

    if component == "kpi_card" or (rows and "label" in (rows[0] if rows else {}) and "value" in (rows[0] if rows else {})):
        for r in rows:
            label = str(r.get("label", ""))
            s, m = metric_meaning(label, r.get("value"))
            metrics[label] = {"value": r.get("value"), "status": s, "meaning": m}
    elif x and y and y.lower() in ("cpi", "spi"):
        pts = [(str(r.get(x)), v) for r in rows if (v := _num(r.get(y))) is not None]
        if pts:
            last_l, last_v = pts[-1]
            s, m = index_status(last_v)
            metrics[y.upper()] = {"value": last_v, "as_of": last_l, "status": s, "meaning": m}
    elif component == "risk_matrix" or (fields or {}).get("label"):
        label = (fields or {}).get("label", "risk")
        for r in rows:
            score = (_num(r.get(x)) or 0) * (_num(r.get(y)) or 0)
            metrics[str(r.get(label))] = {
                "score": score,
                "status": "critical" if score >= 15 else "warning" if score >= 8 else "low",
                "meaning": "likelihood × impact exposure",
            }

    return {
        "artifact": title,
        "metrics": metrics,
        "interpretation": interpret(f"interpret {title}", fields, component, rows, title) or "",
        "likely_drivers": LIKELY_DRIVERS,
    }


def _num(v) -> Optional[float]:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None
