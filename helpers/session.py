import chainlit as cl

_PENDING_KEY = "pending_ui"


def get_pending_ui() -> dict:
    return cl.user_session.get(_PENDING_KEY) or {"actions": [], "elements": []}


def clear_pending_ui():
    cl.user_session.set(_PENDING_KEY, {"actions": [], "elements": []})


def stage_actions(buttons: list):
    state = get_pending_ui()
    state["actions"].extend(buttons)
    cl.user_session.set(_PENDING_KEY, state)


def stage_element(element):
    state = get_pending_ui()
    # One CustomElement per component name per message (avoids generate + display double-render)
    if isinstance(element, cl.CustomElement) and getattr(element, "name", None):
        name = element.name
        state["elements"] = [
            e for e in state["elements"]
            if not (isinstance(e, cl.CustomElement) and getattr(e, "name", None) == name)
        ]
    state["elements"].append(element)
    cl.user_session.set(_PENDING_KEY, state)
