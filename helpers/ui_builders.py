"""Helpers that convert plain-dict args into cl.* objects."""
import chainlit as cl


def build_action(btn: dict) -> cl.Action:
    kwargs = dict(
        name="ui_action",
        label=btn["label"],
        payload={"message": btn.get("message", btn["label"]), "btn_id": btn["id"]},
    )
    if btn.get("icon"):
        kwargs["icon"] = btn["icon"]
    if btn.get("tooltip"):
        kwargs["tooltip"] = btn["tooltip"]
    return cl.Action(**kwargs)


def build_task(task: dict) -> cl.Task:
    status_map = {
        "ready": cl.TaskStatus.READY,
        "running": cl.TaskStatus.RUNNING,
        "done": cl.TaskStatus.DONE,
        "failed": cl.TaskStatus.FAILED,
    }
    status = status_map.get(task.get("status", "ready"), cl.TaskStatus.READY)
    return cl.Task(title=task["title"], status=status)
