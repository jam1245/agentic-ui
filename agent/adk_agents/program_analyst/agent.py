"""Program Analyst — the lead Google ADK agent.

A standard ADK `LlmAgent`, but its model is the internal **Genesis** LLM via LiteLLM (no
Google cloud). It reasons over program data and drives the UI through tools:

  * data tools (get_cpi_trend, …) — fetch rows so it can answer questions with real numbers
  * render_chart — plot a chart/table/card in the user's UI (Contract 1 + artifact)
  * list_artifacts / get_artifact_data — answer follow-ups about charts already shown

This is the "local tools first" lead agent. Genesis specialist assistants
(external_assistant_tool) and an orchestrator with sub_agents come in Phase 2 — the
framework (ADK + LiteLlm→Genesis) is already in place for them to plug into.
"""
from __future__ import annotations

from google.adk.agents import LlmAgent

from ...config.model_config import get_model
from ...tools import data_tools
from ...tools.artifact_tools import get_artifact_data, list_artifacts
from ...tools.placeholder_tools import get_program_context
from ...tools.render_tools import render_chart

INSTRUCTION = """
You are the Program Analyst — a program-management assistant for a program team. You answer
questions about cost, schedule, risk, and program health, and you SHOW the answer as a chart
whenever the user asks to see data.

How to work:
1. When the user asks to see / show / plot / compare data, call `render_chart` once with the
   right component and the data source:
     - trend over time              -> component "line_chart", source get_cpi_trend, fields {x:"month", y:"cpi"}
     - compare control accounts     -> "bar_chart", source get_spi_by_control_account, fields {x:"account", y:"spi"}
     - risks by likelihood × impact -> "risk_matrix", source get_top_risks, fields {x:"likelihood", y:"impact", label:"risk"}
     - headline program health      -> "kpi_card", source get_program_health, fields {}
     - plan vs actual by CAM        -> "variance_table", source get_cam_variance, fields {label:"cam"}
   Use program "P-117" unless the user says otherwise. After it renders, reply with ONE
   sentence of insight — do not re-list the numbers the chart already shows.

2. When the user asks a QUESTION about a chart already on screen ("why did March dip?",
   "which control account is worst?", "explain the difference between Jan and Jun", "summarize
   this for a director", "what should I worry about", "draft a plan"), DO NOT re-plot. Call
   `get_artifact_data` (use `list_artifacts` if unsure which chart) to get the real rows, then
   answer conversationally in 2-5 sentences, citing the exact numbers and giving practical,
   program-relevant guidance.

3. To pull current data without plotting, call the matching data tool directly.

Never invent numbers — always get them from a tool. Be concise and useful.
"""

root_agent = LlmAgent(
    name="program_analyst",
    model=get_model(),
    description="Answers program-management questions and drives charts/dashboards from program data.",
    instruction=INSTRUCTION,
    tools=[
        data_tools.get_cpi_trend,
        data_tools.get_spi_by_control_account,
        data_tools.get_top_risks,
        data_tools.get_program_health,
        data_tools.get_cam_variance,
        render_chart,
        list_artifacts,
        get_artifact_data,
        get_program_context,
    ],
)
