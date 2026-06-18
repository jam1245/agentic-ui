"""HTTP backend that drives the React demos with the internal Genesis LLM.

This is the simplest end-to-end path for *your* stack: the React chat POSTs a message,
this server runs the Genesis agent loop (agent/genesis_agent.py), and returns validated
render payloads + the artifact digests. The browser renders them with the SAME
<AgentUIRenderer> used everywhere else.

Run:
    pip install -r agent/requirements.txt
    # Offline (no key): the server auto-uses the mock client.
    python3 -m uvicorn server.genesis_app:app --port 8800
    # Real Genesis:
    export LLM_API_KEY=...  PM_ASSISTANT_ID=...
    python3 -m uvicorn server.genesis_app:app --port 8800

Then `npm run dev:genesis` and open http://localhost:5173/genesis.html.

Sessions are kept in memory keyed by session_id (one Genesis thread + artifact registry
each). Swap for a real store in production so context survives restarts / scales.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Load .env before reading env vars, so config works the same on Windows/macOS/Linux.
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from agent.genesis_agent import GenesisSession, run_turn  # noqa: E402

app = FastAPI(title="Agent-driven UI — Genesis backend")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

_USE_MOCK = os.getenv("GENESIS_MOCK") == "1" or not (os.getenv("LLM_API_KEY") and os.getenv("PM_ASSISTANT_ID"))


def _make_client():
    if _USE_MOCK:
        from agent.genesis_client import MockGenesisClient

        return MockGenesisClient()
    from agent.genesis_client import GenesisClient

    client = GenesisClient()
    client.start_thread()
    return client


# session_id -> (client, GenesisSession)
_SESSIONS: dict[str, tuple] = {}


def _session(session_id: str):
    if session_id not in _SESSIONS:
        _SESSIONS[session_id] = (_make_client(), GenesisSession())
    return _SESSIONS[session_id]


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "mode": "mock" if _USE_MOCK else "genesis"}


@app.post("/api/chat")
def chat(req: ChatRequest) -> dict:
    client, session = _session(req.session_id)
    result = run_turn(client, session, req.message)
    return {
        "text": result.text,
        "payloads": result.payloads,
        "artifacts": result.artifacts,
        "context_used": result.context_used,
    }


@app.get("/api/artifacts")
def artifacts(session_id: str = "default") -> dict:
    _client, session = _session(session_id)
    return {"artifacts": list(session.state.get("artifacts", {}).values())}
