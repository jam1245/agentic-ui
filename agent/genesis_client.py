"""Client for the internal Genesis Completions API (https://api.ai.us.lmco.com/v1).

Genesis uses a completions endpoint: you POST {"model": "...", "prompt": "..."} to
/completions and get an immediate synchronous text response. This is simpler than the
Assistants API (no threads/runs) but requires managing conversation context client-side.

The agent loop (genesis_agent.py) builds context-aware prompts that include artifacts
and prior turns, so the stateless completions API works for multi-turn conversations.

  * A drop-in MOCK client (`MockGenesisClient`) so the demos run end-to-end with no API
    key — flip to the real client by setting LLM_API_KEY + LLM_MODEL.

Both expose the same interface: `start_thread()` (no-op for completions) and `ask(prompt) -> str`.
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
    """Thin, reusable client over the Genesis Completions API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        *,
        timeout: float = 30.0,
    ):
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.model = model or os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
        self.base_url = (base_url or os.getenv("GENESIS_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        self.thread_id: Optional[str] = None  # kept for interface compatibility
        if not self.api_key:
            raise RuntimeError("LLM_API_KEY is not set (or pass api_key=). Use MockGenesisClient for offline demos.")
        
        # Extract model name without provider prefix (openai/gpt-oss-120b -> gpt-oss-120b)
        self.model_name = self.model.split('/')[-1]

    @property
    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def start_thread(self) -> str:
        """No-op for completions API (stateless). Kept for interface compatibility."""
        self.thread_id = "completions-session"
        return self.thread_id

    def ask(self, prompt: str) -> str:
        """Send prompt to /completions endpoint and return the model's response.
        
        This is a single synchronous POST — no threads, runs, or polling.
        The prompt should include all conversation context (managed by the agent loop).
        """
        if self.thread_id is None:
            self.start_thread()
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "max_tokens": 800,  # Enough for JSON, not excessive
            "temperature": 0.3,  # Lower temp = more deterministic, less reasoning
            "stop": ["\n\n{", "```\n{", "USER QUESTION:", "\n\nWe need", "\n\nThe user"],  # Stop reasoning patterns
        }
        
        response = requests.post(
            f"{self.base_url}/completions",
            headers=self._headers,
            json=payload,
            timeout=self.timeout,
        )
        
        if response.status_code != 200:
            raise RuntimeError(
                f"Genesis completions request failed (status {response.status_code}): {response.text}"
            )
        
        # Parse the OpenAI-style JSON response: {"choices": [{"text": "..."}], ...}
        try:
            response_data = response.json()
            if "choices" in response_data and len(response_data["choices"]) > 0:
                text = response_data["choices"][0]["text"]
                
                # Strip any reasoning/explanation before the JSON
                # Look for the first { and take everything from there
                json_start = text.find("{")
                if json_start > 0:
                    text = text[json_start:]
                
                return text
            else:
                raise RuntimeError(f"Unexpected response format: {response.text}")
        except (KeyError, IndexError, ValueError) as e:
            raise RuntimeError(f"Failed to parse completions response: {e}\nResponse: {response.text}")


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
