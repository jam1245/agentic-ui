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
        self.is_mock = False  # real client; the hybrid loop will call the LLM for prose
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

    def ask(self, prompt: str, *, raw: bool = False, max_tokens: Optional[int] = None) -> str:
        """Send prompt to /completions and return the model's text response.

        Single synchronous POST — no threads/runs/polling. The prompt carries all the
        conversation context (built by the agent loop).

        Args:
            raw: When True, return clean natural-language text (prose mode) — no
                strip-to-`{` and no JSON stop sequences. The hybrid agent uses this for
                summaries and follow-up answers. When False (default), keep the original
                JSON-oriented behavior (strip to the first `{`).
            max_tokens: Override the token budget.
        """
        if self.thread_id is None:
            self.start_thread()

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            # Prose answers can be a few sentences; JSON actions are short. Reasoning models
            # also spend tokens "thinking", so give a comfortable budget.
            "max_tokens": max_tokens or (500 if raw else 1200),
            "temperature": 0.3,
        }
        if not raw:
            # JSON mode: stop the model's chain-of-thought from running on.
            payload["stop"] = ["USER QUESTION:", "\n\nWe need", "\n\nThe user", "\n\nWe have"]

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

        try:
            text = response.json()["choices"][0]["text"]
        except (KeyError, IndexError, ValueError) as e:
            raise RuntimeError(f"Failed to parse completions response: {e}\nResponse: {response.text}")

        if raw:
            return text.strip()
        # JSON mode: drop any reasoning preamble before the first brace.
        json_start = text.find("{")
        return text[json_start:] if json_start > 0 else text


class MockGenesisClient:
    """Offline stand-in. Returns canned action JSON for the canonical demo questions so the
    full pipeline (plan → fetch → render → artifact → follow-up) runs with no API key.

    It pattern-matches the LATEST user question in the prompt. The real GenesisClient
    instead returns whatever the assistant generates; both are parsed identically by the
    agent loop. See agent/genesis_agent.py for the action protocol these strings satisfy.
    """

    def __init__(self, *_args, **_kwargs):
        self.thread_id = "mock-thread"
        self.is_mock = True  # hybrid loop uses deterministic structure + prose, never calls ask()
        self._turn = 0

    def start_thread(self) -> str:
        return self.thread_id

    def ask(self, prompt: str, *, raw: bool = False, max_tokens: Optional[int] = None) -> str:
        # Not used in the hybrid loop (it checks is_mock and uses deterministic prose), but
        # kept so the interface matches the real client. Returns an empty string so any
        # accidental call cleanly falls back to deterministic text.
        return ""
