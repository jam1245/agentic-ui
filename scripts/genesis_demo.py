#!/usr/bin/env python3
"""End-to-end Genesis demo — zero-to-working in one command.

Runs the canonical program-management conversation through the Genesis Assistants API and
prints the validated AgentUIPayloads + the artifact context that powers follow-ups. Proves
the whole pipeline against your internal LLM without any frontend.

OFFLINE (no key needed) — see it work right now:
    python3 scripts/genesis_demo.py --mock

REAL Genesis:
    export LLM_API_KEY=...        # your internal key
    export PM_ASSISTANT_ID=...    # your PM assistant id
    python3 scripts/genesis_demo.py

Shows that the SAME contracts (payloads.py / artifacts.py) and the SAME render payloads are
produced regardless of LLM backend — the React UI never changes.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.genesis_agent import GenesisSession, run_turn  # noqa: E402

CONVERSATION = [
    "Show CPI trend for the last six months.",
    "Why did March dip?",
    "Summarize program health.",
    "Turn that into an executive summary.",
    "Show top risks by likelihood and impact.",
]


def make_client(mock: bool):
    if mock:
        from agent.genesis_client import MockGenesisClient

        return MockGenesisClient()
    from agent.genesis_client import GenesisClient

    client = GenesisClient()
    client.start_thread()
    return client


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mock", action="store_true", help="run offline with canned LLM responses")
    args = parser.parse_args()

    client = make_client(args.mock)
    session = GenesisSession()

    for question in CONVERSATION:
        print("\n" + "=" * 78)
        print(f"USER: {question}")
        result = run_turn(client, session, question)
        print(f"\nASSISTANT: {result.text}")
        for payload in result.payloads:
            print(f"\n  ▶ RENDER [{payload['component']}] '{payload['title']}' "
                  f"(artifactId={payload.get('artifactId')})")
            print("    " + json.dumps(payload, indent=2).replace("\n", "\n    "))

    print("\n" + "=" * 78)
    print("ARTIFACTS the chat agent retains (compact digests fed to future prompts):")
    for d in session.state.get("artifacts", {}).values():
        print(f"  - {d['artifactId']} | {d['title']} | {d['summaryForFutureTurns']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
