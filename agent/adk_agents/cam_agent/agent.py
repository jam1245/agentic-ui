"""CAM sub-agent — Earned Value Management (cost/schedule performance)."""
from .._factory import COMMON_RULES, make_specialist
from ...tools.external_assistant_tool import call_cam_assistant_v2

cam_agent = make_specialist(
    name="cam_agent",
    description="EVM / cost performance: CPI, SPI, cost & schedule variance, EAC, CAM variance.",
    instruction=(
        "You are the CAM Agent, a specialist in Earned Value Management and cost performance "
        "(CPI, SPI, CV/SV, EAC, BCWP/ACWP, control accounts, CAM variance). Plot CPI trend "
        "(line_chart), SPI by control account (bar_chart), and CAM variance (variance_table). "
        "Use call_cam_assistant_v2 for EVM interpretation, compliance, or guidance." + COMMON_RULES
    ),
    data_tool_names=["get_cpi_trend", "get_spi_by_control_account", "get_cam_variance"],
    assistant_caller=call_cam_assistant_v2,
)

root_agent = cam_agent  # for standalone ADK discovery
