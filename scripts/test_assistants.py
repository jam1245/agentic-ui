#!/usr/bin/env python3
"""Test the Genesis specialist assistants in isolation (no ADK, no React).

Confirms your *_ASSISTANT_ID values + the Genesis Assistants API are wired correctly.
Calls each assistant directly and prints the status + a snippet of its reply.

Run from the repo root:
    python  scripts/test_assistants.py            # Windows
    python3 scripts/test_assistants.py            # macOS/Linux

Reads from .env (loaded automatically): LLM_API_KEY (or LM_PLATFORM_API_KEY),
LM_PLATFORM_BASE_URL / GENESIS_BASE_URL, EXT_ASSISTANT_SSL_VERIFY, and the four
*_ASSISTANT_ID values.

  status "completed" + real text  → ✅ wired and the assistant answered
  response "[Mock response …]"     → the gateway returned 501 (Assistants API not enabled)
  status "error"                    → see the message (bad id, auth, network, SSL)
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from agent.tools.external_assistant_tool import (  # noqa: E402
    call_cam_assistant_v2,
    call_pm_assistant_v2,
    call_rcca_assistant_v2,
    call_risk_assistant_v2,
)

CASES = [
    ("CAM",  "CAM_ASSISTANT_ID",  call_cam_assistant_v2,  "Our CPI is 0.94 and EAC variance is -$1.2M. What does this mean and what should we do?"),
    ("PM",   "PM_ASSISTANT_ID",   call_pm_assistant_v2,   "Give a one-paragraph executive read on a program with CPI 0.94, SPI 1.02, 12 open risks."),
    ("Risk", "RISK_ASSISTANT_ID", call_risk_assistant_v2, "Is a supplier-delay risk at likelihood 4, impact 5 typical, and how should we handle it?"),
    ("RCCA", "RCCA_ASSISTANT_ID", call_rcca_assistant_v2, "Give a 5-Whys starting point for a 3-week integration milestone slip."),
]


def main() -> int:
    base = os.getenv("LM_PLATFORM_BASE_URL") or os.getenv("GENESIS_BASE_URL") or "(default)"
    has_key = bool(os.getenv("LLM_API_KEY") or os.getenv("LM_PLATFORM_API_KEY"))
    print(f"Base URL : {base}")
    print(f"API key  : {'set' if has_key else 'MISSING — set LLM_API_KEY in .env'}")
    print("=" * 78)

    any_real = False
    for label, env_name, fn, query in CASES:
        aid = os.getenv(env_name)
        print(f"\n[{label}]  {env_name}={aid or '(not set → placeholder)'}")
        result = fn(query)
        status = result.get("status")
        if status == "completed":
            resp = result.get("response", "")
            if resp.startswith("[Mock response"):
                print(f"  ⚠  {resp}  (gateway returned 501 — Assistants API not enabled for this key)")
            else:
                any_real = True
                print(f"  ✅ {len(resp)} chars: {resp[:300]}")
        else:
            print(f"  ✗  error: {result.get('error')}")

    print("\n" + "=" * 78)
    print("✅ At least one assistant returned a real reply." if any_real
          else "⚠  No real replies — check IDs / key / that the Assistants API is enabled, or run "
               "the chat anyway (sub-agents still plot + interpret from data without the assistants).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
