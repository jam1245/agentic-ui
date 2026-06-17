import os
import json
import chainlit as cl

from .prompts import SYSTEM_PROMPT
from .schemas import ALL_TOOL_SCHEMAS
from .session import get_pending_ui, clear_pending_ui
from .ui_builders import build_action
from . import registry
from .registry import get_step_label
from .jsx_generator import (
    GENERATE_TOOL,
    generate_and_validate_jsx,
    jsx_model_name,
    uses_jsx_model,
)

MAX_ITER = 8


def msg_to_dict(msg) -> dict:
    """Serialize OpenAI message objects (or dicts) for session history."""
    if isinstance(msg, dict):
        return msg
    d = {"role": msg.role, "content": msg.content or ""}
    if getattr(msg, "tool_calls", None):
        d["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.function.name, "arguments": tc.function.arguments},
            }
            for tc in msg.tool_calls
        ]
    if getattr(msg, "tool_call_id", None):
        d["tool_call_id"] = msg.tool_call_id
    return d


async def run_turn_after_ui(client, element: str, action: str, payload: dict):
    """Follow-up turn after user finishes an interactive custom element."""
    detail = json.dumps(payload, ensure_ascii=False) if payload else "{}"
    content = (
        f"[Interactive UI completed — already shown in chat; do NOT display it again]\n"
        f"Element: {element}\n"
        f"User action: {action}\n"
        f"Result data: {detail}\n\n"
        f"Reply in plain text acknowledging what the user did. "
        f"Only call tools if the conversation needs something new and different "
        f"(not display_custom_element or generate_custom_element_code for the same widget)."
    )
    await run_turn(client, cl.Message(content=content))


async def run_turn(client, message: cl.Message):
    history = cl.user_session.get("conversation_history") or []
    history.append({"role": "user", "content": message.content})

    system_prompt = cl.user_session.get("system_prompt") or SYSTEM_PROMPT
    messages = [{"role": "system", "content": system_prompt}] + history
    model = os.environ["LLM_MODEL"]

    response_text = ""

    for _ in range(MAX_ITER):
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            tools=ALL_TOOL_SCHEMAS,
            tool_choice="auto",
            temperature=0.1,
        )

        resp_msg = response.choices[0].message
        messages.append(resp_msg)

        if not resp_msg.tool_calls:
            response_text = resp_msg.content or ""
            break

        for tool_call in resp_msg.tool_calls:
            fn_name = tool_call.function.name
            fn_args = json.loads(tool_call.function.arguments)
            handler, is_ui = registry.get(fn_name)
            step_type = "ui" if is_ui else "tool"
            step_label, step_icon = get_step_label(fn_name)
            planner_spec = fn_args.get("jsx_code", "") if fn_name == GENERATE_TOOL else ""

            step_input = fn_args
            if fn_name == GENERATE_TOOL and uses_jsx_model():
                step_input = {
                    "element_name": fn_args.get("element_name"),
                    "props": fn_args.get("props"),
                    "requirements": planner_spec[:2000] if planner_spec else "",
                    "jsx_generated_by": jsx_model_name(),
                }

            async with cl.Step(name=step_label, type=step_type, show_input="json") as step:
                step.name = step_label
                if step_icon:
                    step.icon = step_icon
                step.input = json.dumps(step_input, indent=2)
                try:
                    if fn_name == GENERATE_TOOL and uses_jsx_model():
                        result, fn_args, _jsx_attempt = await generate_and_validate_jsx(
                            client, handler, fn_args, messages,
                        )
                    else:
                        result = await handler(fn_args)
                    step.output = json.dumps(result, indent=2)
                except Exception as e:
                    result = {"error": str(e), "tool": fn_name}
                    step.output = json.dumps(result, indent=2)
                    clear_pending_ui()
                await step.update()

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result),
            })
    else:
        # MAX_ITER reached without a clean finish
        response_text = "I've completed the available processing steps."

    pending = get_pending_ui()
    actions = [build_action(b) for b in pending.get("actions", [])]
    elements = pending.get("elements", [])

    await cl.Message(
        content=response_text,
        actions=actions or None,
        elements=elements or None,
    ).send()

    # Persist full turn (assistant tool_calls + tool results), not just final text
    cl.user_session.set("conversation_history", [msg_to_dict(m) for m in messages[1:]])
    clear_pending_ui()
