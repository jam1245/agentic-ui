"""Artifact-to-agent context contract (Python side).

Mirror of src/contract/artifact.ts. Where `payloads.py` describes how to *render*,
this describes what a rendered artifact *means* so the main chat agent can reason about
it in later turns.

Storage strategy (the key decision — see docs/09):
  * The compact DIGEST (summary + schema + filters + sample) is what goes into the model's
    context each turn — cheap and prompt-safe.
  * The FULL rows live in the session store, fetched only on demand.
  * For large enterprise datasets, store a `data_ref` (query hash / cache key / URI) and
    re-query the source/MCP tool to rehydrate instead of persisting megabytes.

The registry operates on a plain dict (the per-conversation session store — see
`GenesisSession.state` in genesis_agent.py), so it's testable without any agent runtime.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field

from .payloads import AgentUIPayload

# Key under which the artifact registry lives in the session store.
ARTIFACTS_STATE_KEY = "artifacts"
SAMPLE_SIZE = 5


class ArtifactContext(BaseModel):
    artifactId: str
    artifactType: str
    title: str
    originalUserQuestion: str
    sourceTool: str
    sourceSystem: Optional[str] = None
    dataRef: Optional[str] = None
    dataSample: Optional[list[dict[str, Any]]] = None
    fullData: Optional[list[dict[str, Any]]] = None
    fields: dict[str, str] = Field(default_factory=dict)
    filtersApplied: Optional[dict[str, Any]] = None
    assumptions: Optional[list[str]] = None
    agentInterpretation: str = ""
    summaryForFutureTurns: str = ""
    createdAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ArtifactDigest(BaseModel):
    """Prompt-safe projection — THIS is what the chat agent sees each turn."""

    artifactId: str
    artifactType: str
    title: str
    originalUserQuestion: str
    summary: str
    fields: dict[str, str]
    filtersApplied: Optional[dict[str, Any]] = None
    rowCount: int
    dataSample: Optional[list[dict[str, Any]]] = None
    hasFullData: bool
    createdAt: str


def to_artifact_context(
    payload: AgentUIPayload,
    *,
    original_user_question: str,
    source_tool: str,
    summary_for_future_turns: str,
    source_system: Optional[str] = None,
    data_ref: Optional[str] = None,
    assumptions: Optional[list[str]] = None,
) -> ArtifactContext:
    """Normalize a rendering payload + agent knowledge into an ArtifactContext."""
    data = payload.data
    return ArtifactContext(
        artifactId=payload.artifactId or _new_id(payload.component),
        artifactType=payload.component,
        title=payload.title,
        originalUserQuestion=original_user_question,
        sourceTool=source_tool,
        sourceSystem=source_system or payload.metadata.source,
        dataRef=data_ref,
        dataSample=data[:SAMPLE_SIZE],
        fullData=data,
        fields=payload.fields.model_dump(exclude_none=True) if getattr(payload, "fields", None) else {},
        filtersApplied=payload.metadata.filtersApplied,
        assumptions=assumptions,
        agentInterpretation=payload.metadata.explanation or summary_for_future_turns,
        summaryForFutureTurns=summary_for_future_turns,
    )


def to_digest(a: ArtifactContext) -> ArtifactDigest:
    return ArtifactDigest(
        artifactId=a.artifactId,
        artifactType=a.artifactType,
        title=a.title,
        originalUserQuestion=a.originalUserQuestion,
        summary=a.summaryForFutureTurns,
        fields=a.fields,
        filtersApplied=a.filtersApplied,
        rowCount=len(a.fullData or a.dataSample or []),
        dataSample=a.dataSample,
        hasFullData=bool(a.fullData) or bool(a.dataRef),
        createdAt=a.createdAt,
    )


# ----------------------------------------------------------------------------------
# Session-state registry. `state` is the per-conversation session dict (GenesisSession.
# state). We persist artifacts as plain dicts so they survive serialization across turns.
# ----------------------------------------------------------------------------------

def store_artifact(state: dict, artifact: ArtifactContext) -> None:
    registry: dict[str, Any] = state.get(ARTIFACTS_STATE_KEY) or {}
    registry[artifact.artifactId] = artifact.model_dump(exclude_none=True)
    state[ARTIFACTS_STATE_KEY] = registry


def get_artifact(state: dict, artifact_id: str) -> Optional[ArtifactContext]:
    raw = (state.get(ARTIFACTS_STATE_KEY) or {}).get(artifact_id)
    return ArtifactContext(**raw) if raw else None


def list_digests(state: dict) -> list[ArtifactDigest]:
    registry = state.get(ARTIFACTS_STATE_KEY) or {}
    return [to_digest(ArtifactContext(**raw)) for raw in registry.values()]


_counter = 0


def _new_id(component: str) -> str:
    global _counter
    _counter += 1
    return f"artifact_{component}_{int(datetime.now().timestamp())}_{_counter}"
