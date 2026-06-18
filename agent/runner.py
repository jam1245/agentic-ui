"""Run the ADK Program Analyst agent for one chat turn and extract what the UI needs.

The agent (LlmAgent on Genesis-via-LiteLLM) does its own reasoning + tool-calling. Tools
stage chart payloads and artifacts into ADK session state (see render_tools.py). This module
runs the turn synchronously, then reads the staged `payloads`, `artifacts`, and `context_used`
back out of session state and returns them in the same shape the React client already expects:

    {"text": str, "payloads": [...], "artifacts": [...], "context_used": [...]}

`GENESIS_DEBUG=1` prints the agent's final text.
"""
from __future__ import annotations

import os

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .adk_agents.program_analyst.agent import root_agent
from .artifacts import to_digest, ArtifactContext
from .tools.artifact_tools import ARTIFACTS_KEY, CONTEXT_USED_KEY
from .tools.render_tools import PENDING_KEY

APP_NAME = "program_analyst"
USER_ID = "web"

_session_service = InMemorySessionService()
_runner = Runner(app_name=APP_NAME, agent=root_agent, session_service=_session_service)


def _ensure_session(session_id: str):
    existing = _session_service.get_session_sync(app_name=APP_NAME, user_id=USER_ID, session_id=session_id)
    if existing is None:
        _session_service.create_session_sync(app_name=APP_NAME, user_id=USER_ID, session_id=session_id, state={})


def run_turn(session_id: str, user_message: str) -> dict:
    _ensure_session(session_id)

    # Reset per-turn staging and record the question (render_chart uses it for the artifact).
    state_delta = {PENDING_KEY: [], CONTEXT_USED_KEY: [], "last_user_message": user_message}
    new_message = types.Content(role="user", parts=[types.Part(text=user_message)])

    final_text = ""
    for event in _runner.run(
        user_id=USER_ID, session_id=session_id, new_message=new_message, state_delta=state_delta
    ):
        if event.is_final_response() and event.content and event.content.parts:
            final_text = "".join(p.text or "" for p in event.content.parts).strip()

    if os.getenv("GENESIS_DEBUG") == "1":
        import sys
        print(f"[adk final] {final_text[:400]!r}", file=sys.stderr)

    session = _session_service.get_session_sync(app_name=APP_NAME, user_id=USER_ID, session_id=session_id)
    state = session.state if session else {}

    payloads = list(state.get(PENDING_KEY) or [])
    context_used = list(state.get(CONTEXT_USED_KEY) or [])
    # Compact, prompt-safe digests of every artifact so far (drives the Context panel).
    registry = state.get(ARTIFACTS_KEY) or {}
    artifacts = [to_digest(ArtifactContext(**a)).model_dump(exclude_none=True) for a in registry.values()]

    return {"text": final_text, "payloads": payloads, "artifacts": artifacts, "context_used": context_used}
