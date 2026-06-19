"""PM sub-agent — general program management (health, schedule, summaries). The default host."""
from .._factory import COMMON_RULES, make_specialist
from ...tools.external_assistant_tool import call_pm_assistant_v2

pm_agent = make_specialist(
    name="pm_agent",
    description="Program health, status, executive summaries, schedule/milestones, and general program execution.",
    instruction=(
        "You are the PM Agent — the general program-management host. Handle program health, "
        "status, executive summaries, milestones, and anything that doesn't clearly belong to "
        "another specialist. Plot headline metrics as kpi_card (get_program_health). Use "
        "call_pm_assistant_v2 for leadership briefs, strategy, and program-execution guidance." + COMMON_RULES
    ),
    data_tool_names=["get_program_health"],
    assistant_caller=call_pm_assistant_v2,
)

root_agent = pm_agent
