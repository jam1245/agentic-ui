"""Client for the internal Genesis Assistants API (https://api.ai.us.lmco.com/v1).

Genesis is an OpenAI Assistants-style API: you create a thread, add messages, start a run
against an assistant_id, poll for completion, then read the assistant's reply. This wraps
that flow with two improvements over the one-shot script:

  * Thread REUSE — one thread per conversation, so the assistant retains context across
    turns (needed for artifact-aware follow-ups like "why did March dip?").
  * A drop-in MOCK client (`MockGenesisClient`) so the demos run end-to-end with no API
    key — flip to the real client by setting LLM_API_KEY + PM_ASSISTANT_ID.

Both expose the same interface: `start_thread()` and `ask(prompt) -> str`.
"""
from __future__ import annotations

import os
import time
from typing import Optional

import requests

# Load .env so credentials work the same on Windows/macOS/Linux without `export`/`set`.
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv optional; env vars still work if set directly
    pass

DEFAULT_BASE_URL = "https://api.ai.us.lmco.com/v1"


class GenesisClient:
    """Thin, reusable client over the Genesis Assistants API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        assistant_id: Optional[str] = None,
        base_url: Optional[str] = None,
        *,
        poll_seconds: int = 60,
    ):
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.assistant_id = assistant_id or os.getenv("PM_ASSISTANT_ID")
        self.base_url = (base_url or os.getenv("GENESIS_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.poll_seconds = poll_seconds
        self.thread_id: Optional[str] = None
        if not self.api_key:
            raise RuntimeError("LLM_API_KEY is not set (or pass api_key=). Use MockGenesisClient for offline demos.")
        if not self.assistant_id:
            raise RuntimeError("PM_ASSISTANT_ID is not set (or pass assistant_id=).")

    @property
    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def start_thread(self) -> str:
        """Create a fresh conversation thread and remember it for subsequent asks."""
        resp = requests.post(f"{self.base_url}/threads", headers=self._headers, json={}, timeout=10)
        resp.raise_for_status()
        self.thread_id = resp.json()["id"]
        return self.thread_id

    def ask(self, prompt: str) -> str:
        """Send one prompt on the current thread and return the assistant's text reply."""
        if self.thread_id is None:
            self.start_thread()

        requests.post(
            f"{self.base_url}/threads/{self.thread_id}/messages",
            headers=self._headers,
            json={"role": "user", "content": prompt},
            timeout=10,
        ).raise_for_status()

        run = requests.post(
            f"{self.base_url}/threads/{self.thread_id}/runs",
            headers=self._headers,
            json={"assistant_id": self.assistant_id},
            timeout=30,
        )
        run.raise_for_status()
        run_id = run.json()["id"]

        for _ in range(self.poll_seconds):
            status = requests.get(
                f"{self.base_url}/threads/{self.thread_id}/runs/{run_id}",
                headers=self._headers,
                timeout=10,
            ).json()["status"]
            if status == "completed":
                break
            if status in ("failed", "cancelled", "expired"):
                raise RuntimeError(f"Genesis run {status}")
            time.sleep(1)
        else:
            raise TimeoutError("Genesis run did not complete in time")

        messages = requests.get(
            f"{self.base_url}/threads/{self.thread_id}/messages",
            headers=self._headers,
            timeout=10,
        ).json()["data"]
        # Assistants API returns newest-first; take the latest assistant message.
        for message in messages:
            if message["role"] == "assistant":
                return message["content"][0]["text"]["value"]
        raise RuntimeError("No assistant response found")


class MockGenesisClient:
    """Offline stand-in. Returns canned action JSON for the canonical demo questions so the
    full pipeline (plan → fetch → render → artifact → follow-up) runs with no API key.

    It pattern-matches the LATEST user question in the prompt. The real GenesisClient
    instead returns whatever the assistant generates; both are parsed identically by the
    agent loop. See agent/genesis_agent.py for the action protocol these strings satisfy.
    """

    def __init__(self, *_args, **_kwargs):
        self.thread_id = "mock-thread"
        self._turn = 0

    def start_thread(self) -> str:
        return self.thread_id

    def ask(self, prompt: str) -> str:
        q = _last_user_question(prompt).lower()

        # Follow-up: "why did March dip?" — the agent has already injected artifact context.
        if "march" in q and ("dip" in q or "why" in q):
            if "ROWS FOR ARTIFACT" in prompt:  # second pass: we gave it the rehydrated rows
                return _json(
                    '{"action":"reply","text":"March CPI dipped to 0.91 — the lowest point '
                    "in the window — before recovering. The dip lines up with the late "
                    'requirements baseline noted in the schedule risk."}'
                )
            return _json('{"action":"get_artifact","artifactId":"__latest_line_chart__"}')

        if "executive summary" in q or ("summar" in q and ("that" in q or "kpi" in q)):
            return _json(
                '{"action":"reply","text":"Executive summary — Program health is mixed: '
                "SPI is on track (1.02), but CPI is below target (0.94) and EAC variance is "
                '-$1.2M with 12 open risks. Recommend a cost-recovery review."}'
            )

        if "cpi" in q or "trend" in q:
            return _json(
                '{"action":"fetch_data","tool":"get_cpi_trend","args":{"program":"P-117","months":6},'
                '"then":{"component":"line_chart","title":"CPI Trend — Last 6 Months",'
                '"userIntent":"trend_analysis","fields":{"x":"month","y":"cpi"},'
                '"summary":"CPI rose from 0.92 to 1.01 over six months, with a dip in March.",'
                '"explanation":"Line chart selected because the user asked for a trend over time."}}'
            )
        if "health" in q or "summarize program" in q:
            return _json(
                '{"action":"fetch_data","tool":"get_program_health","args":{"program":"P-117"},'
                '"then":{"component":"kpi_card","title":"Program Health Summary",'
                '"userIntent":"status_summary","fields":{},'
                '"summary":"CPI 0.94 (warning), SPI 1.02 (good), 12 open risks, EAC -$1.2M (critical).",'
                '"explanation":"KPI cards selected for a headline health summary."}}'
            )
        if "risk" in q:
            return _json(
                '{"action":"fetch_data","tool":"get_top_risks","args":{"program":"P-117"},'
                '"then":{"component":"risk_matrix","title":"Top Program Risks",'
                '"userIntent":"distribution","fields":{"x":"likelihood","y":"impact","label":"risk"},'
                '"summary":"Supplier delay (4x5) is the top exposure; staffing gap (3x4) next.",'
                '"explanation":"Risk matrix selected to position risks by likelihood x impact."}}'
            )
        if "spi" in q:
            return _json(
                '{"action":"fetch_data","tool":"get_spi_by_control_account","args":{"program":"P-117"},'
                '"then":{"component":"bar_chart","title":"SPI by Control Account",'
                '"userIntent":"comparison","fields":{"x":"account","y":"spi"},'
                '"summary":"CA-400 is the schedule laggard at 0.86.",'
                '"explanation":"Bar chart selected to compare SPI across control accounts."}}'
            )

        return _json('{"action":"reply","text":"I can chart CPI trends, SPI, risks, or program health. What would you like to see?"}')


def _last_user_question(prompt: str) -> str:
    # The agent loop puts the user's question after a "USER QUESTION:" marker.
    marker = "USER QUESTION:"
    if marker in prompt:
        return prompt.split(marker)[-1].strip().splitlines()[0]
    return prompt.strip().splitlines()[-1] if prompt.strip() else ""


def _json(s: str) -> str:
    return s
