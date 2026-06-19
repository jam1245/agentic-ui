"""Risk (RIO) sub-agent — risk, issue & opportunity analysis."""
from .._factory import COMMON_RULES, make_specialist
from ...tools.external_assistant_tool import call_risk_assistant_v2

risk_agent = make_specialist(
    name="risk_agent",
    description="Risk/Issue/Opportunity: likelihood × impact scoring, 5×5 matrix, mitigation, prioritization.",
    instruction=(
        "You are the RIO Agent, a specialist in Risk, Issue & Opportunity management. Plot top "
        "risks as a risk_matrix (fields x=likelihood, y=impact, label=risk). Help prioritize by "
        "likelihood × impact and recommend mitigation. Use call_risk_assistant_v2 for risk "
        "handling strategy and RIO process guidance." + COMMON_RULES
    ),
    data_tool_names=["get_top_risks"],
    assistant_caller=call_risk_assistant_v2,
)

root_agent = risk_agent
