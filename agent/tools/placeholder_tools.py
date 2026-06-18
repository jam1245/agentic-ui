"""Generic utility tools available to any agent (borrowed from adk-project).

Replace with real platform integrations as they mature.
"""
from __future__ import annotations


def get_program_context() -> dict:
    """Return basic program context/metadata the agent can use before answering."""
    return {"program": "P-117", "status": "active", "phase": "execution",
            "note": "Placeholder — connect to a real data source later."}


def log_agent_action(agent_name: str, action: str) -> str:
    """Record a significant agent action for observability."""
    print(f"[{agent_name}] {action}")
    return f"Logged: {action}"
