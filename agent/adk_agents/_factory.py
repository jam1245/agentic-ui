"""Factory for specialist sub-agents — keeps the per-domain agents thin and consistent.

Every specialist is an ADK `LlmAgent` (Genesis via LiteLLM) that can:
  * fetch its domain data (a subset of the data tools),
  * render charts in the UI (render_chart),
  * answer follow-ups about charts it showed (list/get_artifact_data),
  * consult its pre-built Genesis specialist assistant for deep domain expertise
    (call_*_assistant_v2 from external_assistant_tool).

This is the "plug and play" point: add a new specialist by adding one thin agent.py that
calls `make_specialist(...)`, then list it in the orchestrator's sub_agents.
"""
from __future__ import annotations

from typing import Callable, Optional

from google.adk.agents import LlmAgent

from ._context import with_canvas
from ..config.model_config import get_model
from ..tools import data_tools
from ..tools.artifact_tools import get_artifact_data, list_artifacts
from ..tools.placeholder_tools import get_program_context
from ..tools.render_tools import render_chart

_DATA_TOOLS = {
    "get_cpi_trend": data_tools.get_cpi_trend,
    "get_spi_by_control_account": data_tools.get_spi_by_control_account,
    "get_top_risks": data_tools.get_top_risks,
    "get_program_health": data_tools.get_program_health,
    "get_cam_variance": data_tools.get_cam_variance,
}


def make_specialist(
    *,
    name: str,
    description: str,
    instruction: str,
    data_tool_names: list[str],
    assistant_caller: Optional[Callable] = None,
    extra_tools: Optional[list] = None,
) -> LlmAgent:
    """Build a domain specialist LlmAgent with the shared UI tools + its own data/assistant."""
    tools: list = [_DATA_TOOLS[n] for n in data_tool_names]
    tools += [render_chart, get_artifact_data, list_artifacts, get_program_context]
    if assistant_caller is not None:
        tools.append(assistant_caller)
    if extra_tools:
        tools += extra_tools
    return LlmAgent(
        name=name,
        model=get_model(),
        description=description,
        # Dynamic instruction: the base guidance + the live canvas summary, every turn.
        instruction=with_canvas(instruction),
        tools=tools,
    )


# Shared guidance appended to every specialist's instruction.
COMMON_RULES = """

YOU ARE AN ANALYST, NOT A LOOKUP TOOL. Never just repeat values back. When the user asks
what something means, whether it's good or bad, what's driving it, or what to do, you must
INTERPRET: explain the implication, judge it against program-management thresholds, note
likely drivers and your confidence, and recommend a next action. Write 2-5 substantive
sentences (a director-ready answer), not one line.

Program thresholds to reason with: CPI/SPI of 1.0 is on plan — below 1.0 is unfavorable
(cost/schedule efficiency behind plan), above 1.0 favorable; a negative EAC/cost variance is
a projected overrun; risk exposure = likelihood × impact. Cite the real numbers AND say what
they mean for the program.

How you work:
- To SHOW data, call render_chart (it pulls authoritative rows from a data tool — never
  invent numbers). Then give a brief, substantive read on what the chart shows.
- For a QUESTION about a chart, you already know what's on screen (see "CHARTS CURRENTLY ON
  SCREEN" below). Call get_artifact_data(artifactId) for the full rows, then INTERPRET — and
  reason ACROSS charts where relevant (e.g., relate the cost trend to the top risk).
- For interpretive or domain-expert questions ("what does this mean", "is this good or bad",
  "what's driving this", "what should I do", "is this typical"), CALL YOUR SPECIALIST
  ASSISTANT (the call_*_assistant tool) with the relevant values + the user's question, then
  weave its expert guidance into your answer. This is your primary source of interpretation.
- You OWN this domain. Only defer to another agent if the request is clearly outside it.
- Use program "P-117" unless the user specifies otherwise.
"""
