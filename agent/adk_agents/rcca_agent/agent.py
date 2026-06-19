"""RCCA sub-agent — root cause & corrective action."""
from .._factory import COMMON_RULES, make_specialist
from ...tools.external_assistant_tool import call_rcca_assistant_v2
from ...tools.render_tools import render_structured

rcca_agent = make_specialist(
    name="rcca_agent",
    description="Root cause & corrective action: 5-Whys, fishbone/Ishikawa, 8D, FMEA, corrective action plans.",
    instruction=(
        "You are the RCCA Agent, a specialist in Root Cause & Corrective Action (5-Whys, "
        "fishbone/Ishikawa, 8D, FMEA, CARs). When you've structured the causes, render a "
        "fishbone with render_structured(component='fishbone', problem='<the problem>', "
        "data=[{'category': 'People', 'cause': '...'}, ...], fields={}). Use "
        "call_rcca_assistant_v2 for RCA methodology and corrective-action guidance." + COMMON_RULES
    ),
    data_tool_names=[],
    assistant_caller=call_rcca_assistant_v2,
    extra_tools=[render_structured],
)

root_agent = rcca_agent
