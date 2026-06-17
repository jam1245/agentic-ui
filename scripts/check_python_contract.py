"""Standalone round-trip check for the Python (ADK-side) contracts.

Verifies the data → render payload → ArtifactContext → digest → rehydrate loop WITHOUT
needing google-adk installed (only pydantic). Run:

    python3 -m pip install pydantic
    python3 scripts/check_python_contract.py

Exits non-zero on failure, so it's CI-friendly.
"""
import importlib.util
import sys
import types
from pathlib import Path

# Load agent/payloads.py and agent/artifacts.py as a synthetic package so their relative
# imports resolve, without triggering agent/__init__.py (which imports google.adk).
AGENT_DIR = Path(__file__).resolve().parent.parent / "agent"
pkg = types.ModuleType("ag")
pkg.__path__ = [str(AGENT_DIR)]
sys.modules["ag"] = pkg


def _load(name):
    spec = importlib.util.spec_from_file_location(f"ag.{name}", AGENT_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"ag.{name}"] = module
    spec.loader.exec_module(module)
    return module


_load("payloads")
art = _load("artifacts")
from ag.payloads import FieldMapping, LineChartPayload, PayloadMetadata  # noqa: E402


def main() -> int:
    payload = LineChartPayload(
        artifactId="artifact_cpi_001",
        title="CPI Trend — Last 6 Months",
        data=[
            {"month": "Jan", "cpi": 0.92},
            {"month": "Feb", "cpi": 0.95},
            {"month": "Mar", "cpi": 0.91},
            {"month": "Apr", "cpi": 0.98},
        ],
        fields=FieldMapping(x="month", y="cpi"),
        metadata=PayloadMetadata(source="EVMS MCP", explanation="trend", filtersApplied={"months": 6}),
    )

    artifact = art.to_artifact_context(
        payload,
        original_user_question="Show CPI trend for the last six months.",
        source_tool="evms_mcp.get_cpi_history",
        summary_for_future_turns="CPI rose to 0.98 with a dip in March.",
    )

    state: dict = {}
    art.store_artifact(state, artifact)

    digest = art.list_digests(state)[0]
    assert digest.artifactId == "artifact_cpi_001"
    assert "fullData" not in digest.model_dump(), "digest must NOT carry the full dataset"
    assert digest.rowCount == 4

    rehydrated = art.get_artifact(state, "artifact_cpi_001")
    assert rehydrated is not None
    assert any(r["month"] == "Mar" for r in rehydrated.fullData), "March row must be recoverable"

    print("OK — render → artifact → digest → rehydrate round-trips cleanly.")
    print(f"   digest summary: {digest.summary!r}")
    print(f"   digest carries {len(digest.dataSample or [])} sample rows; full data has {digest.rowCount}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
