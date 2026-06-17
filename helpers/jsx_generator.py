"""Dedicated LLM pass for generate_custom_element_code (uses LLM_MODEL_JSX)."""

from __future__ import annotations

import json
import os
import re

from .schemas import _JSX_GUIDE

GENERATE_TOOL = "generate_custom_element_code"


def jsx_model_name() -> str | None:
    name = os.environ.get("LLM_MODEL_JSX", "").strip()
    return name or None


def uses_jsx_model() -> bool:
    return jsx_model_name() is not None


def last_user_request(messages: list) -> str:
    for msg in reversed(messages):
        if isinstance(msg, dict):
            role, content = msg.get("role"), msg.get("content") or ""
        else:
            role, content = msg.role, msg.content or ""
        if role == "user" and content and not content.startswith("[Interactive UI completed"):
            return content
    return ""


def strip_code_fence(text: str) -> str:
    text = (text or "").strip()
    m = re.search(r"```(?:jsx|javascript|tsx|js)?\s*([\s\S]*?)```", text)
    return m.group(1).strip() if m else text


_JSX_SYSTEM = (
    "You write complete Chainlit custom element .jsx files only. "
    "Output ONLY valid JSX source — no markdown fences, no commentary.\n\n"
    + _JSX_GUIDE
)


def max_jsx_validation_retries() -> int:
    try:
        return max(1, min(int(os.environ.get("JSX_MAX_RETRIES", "3")), 6))
    except ValueError:
        return 3


async def generate_jsx_with_model(
    client,
    *,
    model: str,
    user_request: str,
    element_name: str,
    props: dict | None,
    planner_spec: str | None = None,
    validation_error: str | None = None,
    previous_jsx: str | None = None,
    attempt: int = 1,
) -> str:
    props = props or {}
    spec_block = ""
    if planner_spec and planner_spec.strip():
        spec_block = (
            f"\nPlanner spec (implement fully; no stubs):\n{planner_spec.strip()[:6000]}\n"
        )

    fix_block = ""
    if validation_error:
        fix_block = (
            f"\n\nVALIDATION FAILED on attempt {attempt - 1} — fix this and output the FULL corrected .jsx:\n"
            f"{validation_error.strip()}\n"
        )
        if previous_jsx:
            fix_block += (
                f"\nBroken attempt (rewrite completely; do not repeat the same mistake):\n"
                f"{previous_jsx[:5000]}\n"
            )

    user_msg = (
        f"Build element: {element_name}\n"
        f"User request: {user_request or '(see spec)'}\n"
        f"Props: {json.dumps(props, ensure_ascii=False)}\n"
        f"{spec_block}"
        f"{fix_block}"
    )

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _JSX_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.15 if attempt == 1 else 0.1,
    )
    return strip_code_fence(response.choices[0].message.content or "")


async def generate_and_validate_jsx(client, handler, fn_args: dict, messages: list) -> tuple[dict, dict, int]:
    """Run JSX model + handler validation in a loop until success or retries exhausted."""
    from .session import clear_pending_ui

    jsx_model = jsx_model_name() or ""
    planner_spec = fn_args.get("jsx_code", "")
    user_request = last_user_request(messages)
    element_name = fn_args.get("element_name", "")
    props = fn_args.get("props") or {}

    last_error: str | None = None
    last_jsx: str | None = None
    result: dict = {"error": "JSX generation did not run."}
    max_attempts = max_jsx_validation_retries()
    retry_log: list[dict] = []

    for attempt in range(1, max_attempts + 1):
        fn_args["jsx_code"] = await generate_jsx_with_model(
            client,
            model=jsx_model,
            user_request=user_request,
            element_name=element_name,
            props=props,
            planner_spec=planner_spec if attempt == 1 else None,
            validation_error=last_error,
            previous_jsx=last_jsx,
            attempt=attempt,
        )
        result = await handler(dict(fn_args))
        if not result.get("error"):
            result["jsx_model"] = jsx_model
            result["jsx_attempt"] = attempt
            if retry_log:
                result["validation_retries"] = retry_log
            return result, fn_args, attempt

        last_error = result.get("error", "Unknown validation error.")
        if result.get("required_fix"):
            last_error = f"{last_error}\nFix: {result['required_fix']}"
        retry_log.append({"attempt": attempt, "error": last_error})
        last_jsx = fn_args.get("jsx_code")
        clear_pending_ui()

    result["jsx_model"] = jsx_model
    result["jsx_attempts"] = max_attempts
    result["validation_retries"] = retry_log
    return result, fn_args, max_attempts
