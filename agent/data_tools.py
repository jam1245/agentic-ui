"""Data-layer tools — the MCP/enterprise-system access layer.

These tools do ONE job: retrieve / compute structured data. They return plain dicts
(rows + light metadata). They know nothing about charts. This is the boundary the team
already has working today ("agent calls a tool, gets data back").

In production these wrap real MCP servers (EVMS, Risk Register, IMS). Here they return
representative program-management data so the example is runnable end to end.

The separation is the whole point:
    DATA tools  -> what the numbers ARE                 (this file)
    agent loop  -> picks the chart + answers questions  (genesis_agent.py)
    contracts   -> payload + artifact                   (payloads.py / artifacts.py)
"""
from __future__ import annotations


def get_cpi_trend(program: str, months: int = 6) -> dict:
    """Return monthly Cost Performance Index for a program.

    Args:
        program: Program identifier, e.g. "P-117".
        months: How many trailing months to return.
    """
    # March is a deliberate dip (0.90) so the canonical "why did March dip?" follow-up is
    # truthful against the data the chart was built from.
    series = [0.92, 0.95, 0.90, 0.97, 0.99, 1.01][-months:]
    labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"][-months:]
    return {
        "rows": [{"month": m, "cpi": c} for m, c in zip(labels, series)],
        "source": "EVMS MCP",
        "filters": {"program": program, "months": months},
    }


def get_spi_by_control_account(program: str) -> dict:
    """Return Schedule Performance Index per control account for a program."""
    return {
        "rows": [
            {"account": "CA-100", "spi": 1.04},
            {"account": "CA-200", "spi": 0.91},
            {"account": "CA-300", "spi": 1.00},
            {"account": "CA-400", "spi": 0.86},
        ],
        "source": "EVMS MCP",
        "filters": {"program": program},
    }


def get_top_risks(program: str, limit: int = 10) -> dict:
    """Return the top program risks scored by likelihood (1-5) and impact (1-5)."""
    rows = [
        {"risk": "Supplier delay", "likelihood": 4, "impact": 5},
        {"risk": "Staffing gap", "likelihood": 3, "impact": 4},
        {"risk": "Test rig availability", "likelihood": 2, "impact": 3},
        {"risk": "Scope creep", "likelihood": 4, "impact": 2},
    ]
    return {"rows": rows[:limit], "source": "Risk Register MCP", "filters": {"program": program}}


def get_program_health(program: str) -> dict:
    """Return headline program health metrics with status levels."""
    return {
        "rows": [
            {"label": "CPI", "value": 0.94, "status": "warning"},
            {"label": "SPI", "value": 1.02, "status": "good"},
            {"label": "Open Risks", "value": 12, "status": "warning"},
            {"label": "EAC Variance", "value": "-$1.2M", "status": "critical"},
        ],
        "source": "EVMS MCP",
        "filters": {"program": program},
    }


def get_cam_variance(program: str, period: str) -> dict:
    """Return cost/schedule variance by Control Account Manager for a period."""
    return {
        "rows": [
            {"cam": "J. Rivera", "bcwp": 420, "acwp": 455, "cv": -35, "sv": -10},
            {"cam": "S. Okoye", "bcwp": 610, "acwp": 590, "cv": 20, "sv": 15},
            {"cam": "L. Tan", "bcwp": 300, "acwp": 360, "cv": -60, "sv": -25},
        ],
        "source": "EVMS MCP",
        "filters": {"program": program, "period": period},
    }
