"""Orchestrator — routes each request to the right specialist sub-agent (ADK native
delegation), then the specialist owns the response: it fetches data, renders charts, and
consults its Genesis assistant. This is the plug-and-play core; add a specialist and list it
in `sub_agents`.

The model brain is the internal Genesis LLM via LiteLLM (no Google cloud). `root_agent =
orchestrator` is what `agent/runner.py` runs.
"""
from __future__ import annotations

from google.adk.agents import LlmAgent

from ...config.model_config import get_model
from ..cam_agent.agent import cam_agent
from ..pm_agent.agent import pm_agent
from ..rcca_agent.agent import rcca_agent
from ..risk_agent.agent import risk_agent

INSTRUCTION = """
You are the Program Execution Workbench orchestrator. Route each user request to the single
best specialist sub-agent, then let that specialist answer. You never answer from your own
knowledge — you always delegate.

Specialists:
- cam_agent  — Earned Value Management: CPI, SPI, cost/schedule variance, EAC, CAM variance.
- risk_agent — Risk/Issue/Opportunity: likelihood × impact, risk matrix, mitigation.
- rcca_agent — Root Cause & Corrective Action: 5-Whys, fishbone, 8D, FMEA, CARs.
- pm_agent   — General program management: health, status, executive summaries, schedule,
               and anything that doesn't clearly fit the others. This is the default.

Routing:
- Match the most specific specialist first (cam / risk / rcca own well-defined domains).
- For a multi-domain request, route to the agent that owns the PRIMARY topic.
- When in doubt or for general/program-level questions, route to pm_agent.
- Follow-up questions about a chart already shown go to the SAME specialist that showed it.
"""

orchestrator = LlmAgent(
    name="orchestrator",
    model=get_model(),  # LiteLlm → internal Genesis (no Google cloud)
    description="Routes program-management requests to CAM, Risk, RCCA, or PM specialists.",
    instruction=INSTRUCTION,
    sub_agents=[pm_agent, cam_agent, risk_agent, rcca_agent],
)

root_agent = orchestrator
