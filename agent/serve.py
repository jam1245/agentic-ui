"""Expose the ADK agent over the AG-UI protocol (the Tier-4 backend).

This is the bridge that lets the self-hosted CopilotKit runtime talk to the agent. It
wraps `root_agent` in an AG-UI adapter and serves it as an SSE endpoint: every run is an
HTTP request in, a stream of AG-UI events out (including the `render_ui` tool calls that
become charts in the browser).

Run from the repo root:

    pip install -r agent/requirements.txt
    export GOOGLE_API_KEY=...        # or configure Vertex AI
    uvicorn agent.serve:app --reload --port 8000

Then the CopilotKit runtime (server/copilotkit-runtime.ts) points an HttpAgent at
http://localhost:8000/ and the React chat connects through it. No Copilot Cloud involved —
this is the fully self-hosted, open-source runtime path.
"""
from __future__ import annotations

from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
from fastapi import FastAPI

from .agent import root_agent

# Wrap the ADK agent for AG-UI. In-memory services keep this single-process and simple;
# swap in persistent session/artifact services for production so artifact context (stored
# in tool_context.state by render_ui) survives restarts and scales across instances.
adk_agent = ADKAgent(
    adk_agent=root_agent,
    app_name="program_analyst_app",
    user_id="demo_user",
    session_timeout_seconds=3600,
    use_in_memory_services=True,
)

app = FastAPI(title="Program Analyst — ADK + AG-UI")

# Served at "/", so the AG-UI endpoint is http://localhost:8000/
add_adk_fastapi_endpoint(app, adk_agent, path="/")
