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

How you work:
- To SHOW data, call render_chart (it pulls authoritative rows from a data tool — never
  invent numbers). Then give ONE sentence of insight; don't re-list what the chart shows.
- For a QUESTION about a chart, you ALREADY KNOW what's on screen (see "CHARTS CURRENTLY ON
  SCREEN" below). Call get_artifact_data(artifactId) to pull a chart's full rows, then answer
  conversationally with real numbers. For broader questions, reason ACROSS multiple charts
  and connect them (e.g., relate cost performance to risk or schedule).
- For deep domain expertise or guidance, consult your specialist assistant tool.
- You OWN this domain. Only defer to another agent if the request is clearly outside it.
- Use program "P-117" unless the user specifies otherwise.
"""
