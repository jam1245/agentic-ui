"""HTTP backend for the React UI.

Two execution paths, same response shape:

  * REAL (a Genesis key is set): a Google ADK agent — `agent/adk_agents/program_analyst`,
    brained by the internal Genesis LLM via LiteLLM — reasons, calls data tools, and drives
    charts through the `render_chart` tool. This is the ADK framework the architecture is
    built on (orchestrator + plug-and-play sub-agents come next).
  * MOCK (GENESIS_MOCK=1 or no key): a deterministic engine (agent/genesis_agent.py) so the
    demo and CI run with zero credentials and no live LLM.

Both return { text, payloads, artifacts, context_used } so React, the contract, and the
renderers are identical regardless of path.

Run:
    pip install -r agent/requirements.txt
    python3 -m uvicorn server.genesis_app:app --port 8800     # mock unless a key is set
    # Real ADK+Genesis: set LLM_API_KEY (+ LLM_MODEL, LLM_API_BASE) in .env, then run.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from pydantic import BaseModel  # noqa: E402

app = FastAPI(title="Agent-driven UI — backend")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Force the deterministic engine when there's no key, or when explicitly requested, or if
# ADK isn't importable. Otherwise use the real ADK + Genesis agent.
_USE_MOCK = os.getenv("GENESIS_MOCK") == "1" or not os.getenv("LLM_API_KEY")
_MODE = "mock"
_ADK_ERROR: str | None = None
_WHY_MOCK = (
    "GENESIS_MOCK=1" if os.getenv("GENESIS_MOCK") == "1"
    else "LLM_API_KEY not set" if not os.getenv("LLM_API_KEY")
    else None
)

if not _USE_MOCK:
    try:
        from agent.runner import run_turn as _adk_run_turn  # noqa: E402

        _MODE = "adk"
    except Exception as exc:  # noqa: BLE001
        import traceback
        _ADK_ERROR = f"{type(exc).__name__}: {exc}"
        _WHY_MOCK = f"ADK failed to import — {_ADK_ERROR}"
        _USE_MOCK = True
        print("\n" + "=" * 78)
        print("[backend] ⚠  ADK agent could NOT load — falling back to the DETERMINISTIC engine.")
        print("[backend]    Answers will be curt/computed, not LLM-reasoned. Likely fix:")
        print("[backend]    pip install -r agent/requirements.txt   (installs google-adk + litellm)")
        print(f"[backend]    error: {_ADK_ERROR}")
        traceback.print_exc()
        print("=" * 78 + "\n")

# Loud, unambiguous startup banner so you always know which engine is answering.
print("\n" + "─" * 78)
print(f"[backend] ENGINE = {_MODE.upper()}" + (f"  (reason: {_WHY_MOCK})" if _USE_MOCK else "  (Google ADK + Genesis LLM)"))
print(f"[backend] check any time:  curl http://localhost:8800/api/health")
print("─" * 78 + "\n")

if _USE_MOCK:
    from agent.genesis_agent import GenesisSession, run_turn as _det_run_turn  # noqa: E402

    _SESSIONS: dict[str, GenesisSession] = {}

    def _det_turn(session_id: str, message: str) -> dict:
        session = _SESSIONS.setdefault(session_id, GenesisSession())
        r = _det_run_turn(_mock_client(), session, message)
        return {"text": r.text, "payloads": r.payloads, "artifacts": r.artifacts, "context_used": r.context_used}

    def _mock_client():
        from agent.genesis_client import MockGenesisClient

        return MockGenesisClient()


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


@app.get("/api/health")
def health() -> dict:
    # `mode` is "adk" (real Google ADK + Genesis) or "mock" (deterministic, no LLM).
    # If you expected "adk" but see "mock", read `why` / `adk_error`.
    return {"ok": True, "mode": _MODE, "why": _WHY_MOCK, "adk_error": _ADK_ERROR}


@app.post("/api/chat")
def chat(req: ChatRequest) -> dict:
    if _USE_MOCK:
        return _det_turn(req.session_id, req.message)
    return _adk_run_turn(req.session_id, req.message)
