"""
Register @cl.action_callback handlers. Called once at import time via register_callbacks().
All handlers funnel user interaction back into the agent loop as synthetic user messages.
"""
import os
import chainlit as cl

from .agent import run_turn_after_ui


def register_callbacks(run_turn, client):
    @cl.action_callback("ui_action")
    async def on_ui_action(action: cl.Action):
        """Handles all display_actions buttons (they all share the name 'ui_action')."""
        content = action.payload.get("message") or action.payload.get("btn_id") or action.label
        await run_turn(client, cl.Message(content=content))

    @cl.action_callback("rating_submit")
    async def on_rating_submit(action: cl.Action):
        rating = action.payload.get("rating", "?")
        await run_turn(client, cl.Message(content=f"User gave a rating of {rating} out of 5."))

    @cl.action_callback("tile_captcha_submit")
    async def on_tile_captcha_submit(action: cl.Action):
        p = action.payload or {}
        if p.get("valid"):
            await run_turn(client, cl.Message(content="User completed the tile captcha successfully."))
        else:
            await run_turn(
                client,
                cl.Message(content="User submitted the tile captcha but did not select the correct tiles."),
            )

    @cl.action_callback("consent_submit")
    async def on_consent_submit(action: cl.Action):
        payload = action.payload or {}
        fields_text = ", ".join(f"{k}: {v}" for k, v in payload.items() if k != "submitted")
        content = f"User submitted the form with: {fields_text}" if fields_text else "User submitted the form."
        await run_turn(client, cl.Message(content=content))

    @cl.action_callback("dropdown_select")
    async def on_dropdown_select(action: cl.Action):
        selected = action.payload.get("label") or action.payload.get("selected", "")
        await run_turn(client, cl.Message(content=f"User selected: {selected}"))

    @cl.action_callback("checkbox_submit")
    async def on_checkbox_submit(action: cl.Action):
        selected = action.payload.get("selected", [])
        items_text = ", ".join(selected) if selected else "nothing"
        await run_turn(client, cl.Message(content=f"User selected: {items_text}"))

    @cl.action_callback("rank_submit")
    async def on_rank_submit(action: cl.Action):
        ranked = action.payload.get("ranked", [])
        lines = "\n".join(f"{i+1}. {item}" for i, item in enumerate(ranked))
        await run_turn(client, cl.Message(content=f"User ranked the items:\n{lines}"))

    @cl.action_callback("categories_submit")
    async def on_categories_submit(action: cl.Action):
        columns = action.payload.get("columns", [])
        lines = "\n".join(
            f"{col['name']}: {', '.join(col['items']) or 'empty'}"
            for col in columns
        )
        await run_turn(client, cl.Message(content=f"User categorized items:\n{lines}"))

    @cl.action_callback("record_editor_save")
    async def on_record_editor_save(action: cl.Action):
        p = action.payload or {}
        items = p.get("items") or p.get("key_results") or []
        done = sum(1 for x in items if x.get("complete"))
        await run_turn(
            client,
            cl.Message(content=f"Record saved: '{p.get('title')}' — status: {p.get('status')}, {done}/{len(items)} items complete."),
        )

    @cl.action_callback("record_editor_status")
    async def on_record_editor_status(action: cl.Action):
        p = action.payload or {}
        await run_turn(client, cl.Message(content=f"Record '{p.get('title')}' status: {p.get('status')}"))

    @cl.action_callback("goal_card_save")
    async def on_goal_card_save(action: cl.Action):
        await on_record_editor_save(action)

    @cl.action_callback("goal_status_update")
    async def on_goal_status_update(action: cl.Action):
        p = action.payload or {}
        await run_turn(client, cl.Message(content=f"Record '{p.get('title')}' status: {p.get('status')}"))

    @cl.action_callback("stat_grid_select")
    async def on_stat_grid_select(action: cl.Action):
        p = action.payload or {}
        await run_turn(client, cl.Message(content=f"User selected metric: {p.get('label')} ({p.get('value')})"))

    @cl.action_callback("progress_list_select")
    async def on_progress_list_select(action: cl.Action):
        p = action.payload or {}
        title = p.get("title", "item")
        await run_turn(client, cl.Message(content=f"User selected: {title}"))

    @cl.action_callback("goal_select")
    async def on_goal_select(action: cl.Action):
        p = action.payload or {}
        await run_turn(client, cl.Message(content=f"User selected: {p.get('title')}"))

    @cl.action_callback("highlight_card_submit")
    async def on_highlight_card_submit(action: cl.Action):
        p = action.payload or {}
        headline = p.get("headline", "Highlight")
        name = p.get("nominee_name") or p.get("name", "")
        reason = p.get("reason", "")
        await run_turn(
            client,
            cl.Message(content=f"{headline} — submission from {name}. {reason}".strip()),
        )

    @cl.action_callback("award_nominate")
    async def on_award_nominate(action: cl.Action):
        p = action.payload or {}
        await run_turn(
            client,
            cl.Message(content=f"Nomination: {p.get('nominee_name')} for {p.get('award_name')}. Reason: {p.get('reason', '')}"),
        )

    # feedback_request_submit archived with FeedbackRequestPicker

    @cl.action_callback("gantt_update")
    async def on_gantt_update(action: cl.Action):
        p = action.payload or {}
        changes = p.get("changes", [])
        if changes:
            lines = "\n".join(
                f"- {c['title']}: {c['original_end_date']} → {c['new_end_date']}"
                for c in changes
            )
            await run_turn(client, cl.Message(content=f"I updated the following target dates on the timeline:\n{lines}"))
        else:
            await run_turn(client, cl.Message(content="Timeline confirmed with no changes."))

    @cl.action_callback("card_picker_submit")
    async def on_card_picker_submit(action: cl.Action):
        p = dict(action.payload or {})
        items = p.get("selected_items", [])
        names = ", ".join(i.get("name", str(i)) for i in items) if items else "none"
        await run_turn_after_ui(client, "CardPicker", "selected", {"selected_names": names, **p})

    @cl.action_callback("rating_matrix_submit")
    async def on_rating_matrix_submit(action: cl.Action):
        p = action.payload or {}
        ratings = p.get("ratings", [])
        title = p.get("title", "Ratings")
        summary = ", ".join(f"{r.get('label', r.get('competency', ''))}: {r.get('rating')}/5" for r in ratings)
        await run_turn(client, cl.Message(content=f"{title} submitted: {summary}"))

    @cl.action_callback("competency_ratings_submit")
    async def on_competency_ratings_submit(action: cl.Action):
        p = action.payload or {}
        if p.get("ratings") and p["ratings"][0].get("label"):
            await on_rating_matrix_submit(action)
            return
        ratings = p.get("ratings", [])
        summary = ", ".join(f"{r.get('competency', '')}: {r.get('rating')}/5" for r in ratings)
        await run_turn(client, cl.Message(content=f"Ratings submitted: {summary}"))

    @cl.action_callback("form_submit")
    async def on_form_submit(action: cl.Action):
        p = action.payload or {}
        fields = p.get("fields", [])
        form_title = p.get("title", "Form")
        parts = []
        for f in fields:
            label = f.get("label", f.get("id", ""))
            val = f.get("value")
            if isinstance(val, list):
                val = ", ".join(str(x) for x in val)
            elif isinstance(val, bool):
                val = "yes" if val else "no"
            parts.append(f"{label}: {val}")
        summary = "; ".join(parts) if parts else "no fields"
        await run_turn(client, cl.Message(content=f"{form_title} submitted — {summary}"))

    @cl.action_callback("assessment_submit")
    async def on_assessment_submit(action: cl.Action):
        sections = action.payload.get("sections", [])
        titles = ", ".join(s.get("title", s.get("label", "")) for s in sections)
        await run_turn(client, cl.Message(content=f"Form submitted. Sections: {titles}"))

    @cl.action_callback("tier_picker_submit")
    async def on_tier_picker_submit(action: cl.Action):
        p = action.payload or {}
        title = p.get("title", "Selection")
        await run_turn(
            client,
            cl.Message(content=f"{title}: {p.get('tier_label')} ({p.get('value')}). Comment: {p.get('comment', '')}"),
        )

    @cl.action_callback("performance_rating_submit")
    async def on_performance_rating_submit(action: cl.Action):
        p = action.payload or {}
        if p.get("tier_label") or p.get("value"):
            await on_tier_picker_submit(action)
            return
        emp = f" for {p['employee']}" if p.get("employee") else ""
        await run_turn(
            client,
            cl.Message(content=f"Rating submitted{emp}: {p.get('tier_label', p.get('rating'))}. {p.get('justification', '')}"),
        )

    @cl.action_callback("editable_list_submit")
    async def on_editable_list_submit(action: cl.Action):
        p = action.payload or {}
        title = p.get("title", "List")
        preset = p.get("preset", "")
        if preset == "tasks":
            await run_turn(client, cl.Message(content=f"{title}: {p.get('completed', 0)} of {p.get('total', 0)} items updated."))
        else:
            rows = p.get("rows") or p.get("topics") or []
            labels = ", ".join(t.get("title", "") for t in rows if t.get("title"))
            await run_turn(client, cl.Message(content=f"{title} submitted ({p.get('total_minutes', 0)} min): {labels}"))

    @cl.action_callback("checkin_agenda_submit")
    async def on_checkin_agenda_submit(action: cl.Action):
        p = action.payload or {}
        if p.get("rows") or p.get("preset"):
            await on_editable_list_submit(action)
            return
        topics = p.get("topics", [])
        titles = ", ".join(t["title"] for t in topics if t.get("title"))
        total = p.get("total_minutes", 0)
        await run_turn(client, cl.Message(content=f"Agenda submitted ({total} min): {titles}"))

    @cl.action_callback("action_items_submit")
    async def on_action_items_submit(action: cl.Action):
        p = action.payload or {}
        if p.get("rows") or p.get("preset"):
            await on_editable_list_submit(action)
            return
        await run_turn(client, cl.Message(content=f"Items updated: {p.get('completed', 0)} of {p.get('total', 0)} complete."))

    @cl.action_callback("xlsx_download")
    async def on_xlsx_download(action: cl.Action):
        p = action.payload or {}
        session_key = p.get("session_key", "latest_xlsx")
        file_info = cl.user_session.get(session_key) or cl.user_session.get("latest_xlsx")
        if not file_info:
            await cl.Message(content="Spreadsheet not found. Please regenerate it.").send()
            return
        path = file_info.get("path", "")
        filename = file_info.get("filename", "spreadsheet.xlsx")
        if not path or not os.path.exists(path):
            await cl.Message(content="Spreadsheet file not found. Please regenerate it.").send()
            return
        await cl.Message(
            content="Here is your spreadsheet:",
            elements=[cl.File(
                name=filename, path=path, display="inline",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )],
        ).send()

    @cl.action_callback("word_doc_download")
    async def on_word_doc_download(action: cl.Action):
        p = action.payload or {}
        session_key = p.get("session_key", "latest_word_doc")
        doc_info = cl.user_session.get(session_key) or cl.user_session.get("latest_word_doc")
        if not doc_info:
            await cl.Message(content="Document not found. Please regenerate it.").send()
            return
        path = doc_info.get("path", "")
        filename = doc_info.get("filename", "document.docx")
        if not path or not os.path.exists(path):
            await cl.Message(content="Document file not found. Please regenerate it.").send()
            return
        await cl.Message(
            content="Here is your document:",
            elements=[cl.File(
                name=filename, path=path, display="inline",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )],
        ).send()

    @cl.action_callback("calendar_month_select")
    async def on_calendar_month_select(action: cl.Action):
        p = action.payload or {}
        date = p.get("date", "")
        month = p.get("month", "")
        year = p.get("year", "")
        await run_turn(client, cl.Message(content=f"User selected {month} {year}. Last day of the month: {date}"))

    # Only these actions (or payload.done === true) start a new LLM turn.
    _GENERATED_FINAL = frozenset({
        "verified", "submitted", "confirmed", "done", "finished", "complete",
    })

    @cl.action_callback("generated_element_action")
    async def on_generated_element_action(action: cl.Action):
        p = dict(action.payload or {})
        if not p.get("done") and p.get("action") not in _GENERATED_FINAL:
            return
        action_label = p.pop("action", "finished")
        p.pop("done", None)
        element = p.pop("element", p.pop("element_name", "CustomElement"))
        await run_turn_after_ui(client, element, action_label, p)
