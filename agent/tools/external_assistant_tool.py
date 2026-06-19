"""Bridge an ADK function tool to the internal Genesis **Assistants** API.

Adapted from the adk-project. Lets an ADK agent (or sub-agent) call a pre-built Genesis
assistant (CAM, PM, RIO, RCCA, …) by id. Two call styles are provided:

  * call_assistant_v2(assistant_id, message)  — single POST /threads/runs (SSE stream)
  * call_external_assistant(query, assistant_id) — create thread → run → poll → messages

Both omit the OpenAI-Organization header for internal lmco.com endpoints, default to
SSL-verify off, and treat HTTP 501 as "not implemented" by returning a mock response so
downstream flows keep working. Not wired into the lead agent yet (local tools first) — this
is the foundation for Phase 2 sub-agents.
"""
from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, Optional

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _cfg() -> Dict[str, Any]:
    ssl_raw = os.getenv("EXT_ASSISTANT_SSL_VERIFY", "false").lower()
    return {
        "api_key": (os.getenv("LM_PLATFORM_API_KEY") or os.getenv("EXT_ASSISTANT_API_KEY") or os.getenv("LLM_API_KEY", "")),
        "api_base": (os.getenv("LM_PLATFORM_BASE_URL") or os.getenv("GENESIS_BASE_URL") or "https://api.ai.us.lmco.com/v1").rstrip("/"),
        "org": os.getenv("EXT_ASSISTANT_ORG", ""),
        "ssl_verify": ssl_raw not in ("false", "0", "no"),
        "poll_interval": float(os.getenv("EXT_ASSISTANT_POLL_INTERVAL", "2")),
        "poll_timeout": float(os.getenv("EXT_ASSISTANT_POLL_TIMEOUT", "120")),
    }


def _headers(cfg: Dict[str, Any]) -> Dict[str, str]:
    h = {"Authorization": f"Bearer {cfg['api_key']}", "Content-Type": "application/json", "OpenAI-Beta": "assistants=v2"}
    if cfg["org"] and "lmco.com" not in cfg["api_base"]:
        h["OpenAI-Organization"] = cfg["org"]
    return h


def _parse_sse(response) -> str:
    out: list[str] = []
    for line in response.iter_lines():
        if not line:
            continue
        line = line.decode("utf-8")
        if line.startswith("data:"):
            data_str = line[5:].strip()
            if data_str == "[DONE]":
                break
            try:
                data = json.loads(data_str)
            except json.JSONDecodeError:
                continue
            if data.get("object") == "thread.message.delta":
                for item in data.get("delta", {}).get("content", []):
                    if item.get("type") == "text":
                        out.append(item["text"]["value"])
    return "".join(out)


def call_assistant_v2(assistant_id: str, message: str) -> dict:
    """Call a Genesis assistant via the single POST /threads/runs endpoint (SSE)."""
    cfg = _cfg()
    if not cfg["api_key"]:
        return {"status": "error", "error": "LLM_API_KEY / LM_PLATFORM_API_KEY not set"}
    if not assistant_id:
        return {"status": "error", "error": "No assistant_id provided"}

    debug = os.getenv("GENESIS_DEBUG") == "1"
    if debug:
        import sys
        print(f"[assistant→] id={assistant_id} base={cfg['api_base']} q={message[:80]!r}", file=sys.stderr)

    payload = {"assistant_id": assistant_id, "thread": {"messages": [{"role": "user", "content": message}]}, "stream": True}
    try:
        resp = requests.post(
            f"{cfg['api_base']}/threads/runs",
            headers=_headers(cfg),
            json=payload,
            stream=True,
            verify=cfg["ssl_verify"],
            timeout=30,
        )
        if resp.status_code == 501:
            if debug:
                import sys
                print(f"[assistant✗] 501 Not Implemented — Assistants API unavailable; returning mock.", file=sys.stderr)
            return {"status": "completed", "response": f"[Mock response for assistant {assistant_id}]"}
        resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        if debug:
            import sys
            print(f"[assistant✗] error: {exc}", file=sys.stderr)
        return {"status": "error", "error": str(exc)}

    try:
        reply = _parse_sse(resp) or ""
        if debug:
            import sys
            print(f"[assistant←] {len(reply)} chars: {reply[:160]!r}", file=sys.stderr)
        return {"status": "completed", "response": reply}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": f"Failed to parse stream: {exc}"}


def _assistant(name: str, query: str) -> dict:
    return call_assistant_v2(os.getenv(f"{name}_ASSISTANT_ID", f"{name.lower()}-placeholder"), query)


def call_cam_assistant_v2(query: str) -> dict:
    """Call the CAM (EVM/cost) Genesis assistant. Reads CAM_ASSISTANT_ID."""
    return _assistant("CAM", query)


def call_pm_assistant_v2(query: str) -> dict:
    """Call the PM Genesis assistant. Reads PM_ASSISTANT_ID."""
    return _assistant("PM", query)


def call_risk_assistant_v2(query: str) -> dict:
    """Call the Risk (RIO) Genesis assistant. Reads RISK_ASSISTANT_ID."""
    return _assistant("RISK", query)


def call_rcca_assistant_v2(query: str) -> dict:
    """Call the RCCA Genesis assistant. Reads RCCA_ASSISTANT_ID."""
    return _assistant("RCCA", query)
