from . import data_handlers, ui_handlers

# Maps tool name -> (async handler, is_ui)
_REGISTRY: dict[str, tuple] = {
    # utility
    "rename_thread": (ui_handlers.rename_thread, False),
    # document / file generation
    "generate_word_doc": (ui_handlers.generate_word_doc, True),
    "generate_xlsx": (ui_handlers.generate_xlsx, True),
    # visual timeline
    "display_gantt_timeline": (ui_handlers.display_gantt_timeline, True),
    # custom plotly chart from LLM data
    "display_plotly_chart": (ui_handlers.display_plotly_chart, True),
    # dynamic JSX element generation
    "generate_custom_element_code": (ui_handlers.generate_custom_element_code, True),
    # data tools
    "get_random_numbers": (data_handlers.get_random_numbers, False),
    "fetch_iconify_icons": (data_handlers.fetch_iconify_icons, False),
    "fetch_sample_dataframe": (data_handlers.fetch_sample_dataframe, False),
    "build_sample_plotly_figure": (data_handlers.build_sample_plotly_figure, False),
    "get_sample_file_path": (data_handlers.get_sample_file_path, False),
    # ui display tools
    "display_actions": (ui_handlers.display_actions, True),
    "display_dataframe": (ui_handlers.display_dataframe, True),
    "display_plotly": (ui_handlers.display_plotly, True),
    "display_pyplot": (ui_handlers.display_pyplot, True),
    "display_pdf": (ui_handlers.display_pdf, True),
    "display_file": (ui_handlers.display_file, True),
    "display_custom_element": (ui_handlers.display_custom_element, True),
    "display_tasklist": (ui_handlers.display_tasklist, True),
    "display_text_element": (ui_handlers.display_text_element, True),
    "display_code_block": (ui_handlers.display_code_block, True),
    "display_dropdown": (ui_handlers.display_dropdown, True),
    "display_checkbox": (ui_handlers.display_checkbox, True),
    "display_rank": (ui_handlers.display_rank, True),
    "display_categories": (ui_handlers.display_categories, True),
    "display_record_editor": (ui_handlers.display_record_editor, True),
    "display_stat_grid": (ui_handlers.display_stat_grid, True),
    "display_goal_card": (ui_handlers.display_goal_card, True),
    "display_progress_list": (ui_handlers.display_progress_list, True),
    "display_goal_progress": (ui_handlers.display_goal_progress, True),
    "display_tree": (ui_handlers.display_tree, True),
    "display_okr_tree": (ui_handlers.display_okr_tree, True),
    # "display_feedback_picker" archived — use display_card_picker
    "display_rating_matrix": (ui_handlers.display_rating_matrix, True),
    "display_competency_rater": (ui_handlers.display_competency_rater, True),
    # "display_feedback_card" archived — use display_section_card
    # "display_feedback_summary" archived — use display_pill_board
    "display_section_card": (ui_handlers.display_section_card, True),
    "display_pill_board": (ui_handlers.display_pill_board, True),
    "display_card_picker": (ui_handlers.display_card_picker, True),
    "display_form": (ui_handlers.display_form, True),
    "display_assessment_form": (ui_handlers.display_assessment_form, True),
    "display_tier_picker": (ui_handlers.display_tier_picker, True),
    "display_performance_rating": (ui_handlers.display_performance_rating, True),
    "display_editable_list": (ui_handlers.display_editable_list, True),
    "display_checkin_agenda": (ui_handlers.display_checkin_agenda, True),
    "display_action_items": (ui_handlers.display_action_items, True),
    "display_highlight_card": (ui_handlers.display_highlight_card, True),
    "display_award_card": (ui_handlers.display_award_card, True),
    "display_timeline": (ui_handlers.display_timeline, True),
    "display_date_list": (ui_handlers.display_date_list, True),
    "display_deadline_countdown": (ui_handlers.display_deadline_countdown, True),
    "display_year_calendar": (ui_handlers.display_year_calendar, True),
    # ui ask tools
    "ask_user": (ui_handlers.ask_user, True),
    "ask_file": (ui_handlers.ask_file, True),
    "ask_action": (ui_handlers.ask_action, True),
    "ask_element": (ui_handlers.ask_element, True),
}

# Maps tool name -> (display label, lucide icon name)
_STEP_LABELS: dict[str, tuple[str, str]] = {
    "rename_thread":             ("Rename Chat",          "pencil"),
    "generate_word_doc":         ("Generate Word Doc",    "file-text"),
    "generate_xlsx":             ("Generate Spreadsheet", "table"),
    "display_gantt_timeline":    ("Timeline Chart",       "calendar-range"),
    "display_plotly_chart":         ("Show Chart",           "chart-column"),
    "generate_custom_element_code": ("Build Custom UI",      "code"),
    "get_random_numbers":        ("Random Numbers",       "shuffle"),
    "fetch_iconify_icons":       ("Icons",        "search"),
    "fetch_sample_dataframe":    ("Load Dataset",         "database"),
    "build_sample_plotly_figure":("Build Chart",          "bar-chart-2"),
    "get_sample_file_path":      ("Get File",             "file"),
    "display_actions":           ("Show Buttons",         "square-mouse-pointer"),
    "display_dataframe":         ("Show Table",           "table-2"),
    "display_plotly":            ("Show Chart",           "chart-line"),
    "display_pyplot":            ("Show Chart",           "chart-bar"),
    "display_pdf":               ("Show PDF",             "file-text"),
    "display_file":              ("Attach File",          "paperclip"),
    "display_custom_element":    ("Custom Element",       "blocks"),
    "display_tasklist":          ("Task List",            "list-checks"),
    "display_text_element":      ("Text Panel",           "align-left"),
    "display_code_block":        ("Code Block",           "code"),
    "display_dropdown":          ("Dropdown",             "chevrons-up-down"),
    "display_checkbox":          ("Checkboxes",           "square-check"),
    "display_rank":              ("Rank List",            "arrow-up-down"),
    "display_categories":        ("Category Board",       "columns-2"),
    "display_year_calendar":     ("Month Picker",         "calendar"),
    "display_record_editor":     ("Record Editor",        "file-pen"),
    "display_stat_grid":         ("Metric Grid",          "layout-grid"),
    "display_goal_card":         ("Goal Card",            "target"),
    "display_progress_list":     ("Progress List",        "trending-up"),
    "display_goal_progress":     ("Progress List",        "trending-up"),
    "display_tree":              ("Tree",                 "git-branch"),
    "display_okr_tree":          ("Tree",                 "git-branch"),
    "display_rating_matrix":     ("Rating Matrix",        "star"),
    "display_competency_rater":  ("Rating Matrix",        "star"),
    "display_section_card":      ("Info Card",            "layout-template"),
    "display_pill_board":        ("Theme Board",          "tag"),
    "display_card_picker":       ("Card Picker",          "users"),
    "display_form":              ("Form",                 "clipboard-list"),
    "display_assessment_form":   ("Form",                 "clipboard-list"),
    "display_tier_picker":       ("Tier Picker",          "list-ordered"),
    "display_performance_rating":("Tier Picker",          "list-ordered"),
    "display_editable_list":     ("Editable List",        "list"),
    "display_checkin_agenda":    ("Editable List",        "list"),
    "display_action_items":      ("Editable List",        "list"),
    "display_highlight_card":    ("Highlight Card",       "sparkles"),
    "display_award_card":        ("Highlight Card",       "sparkles"),
    "display_timeline":          ("Event Timeline",       "milestone"),
    "display_date_list":         ("Date List",            "clock"),
    "display_deadline_countdown":("Date List",            "clock"),
    "ask_user":                  ("Ask Question",         "message-circle"),
    "ask_file":                  ("Request File",         "upload"),
    "ask_action":                ("Ask for Choice",       "hand-pointer"),
    "ask_element":               ("Ask Form",             "clipboard-list"),
}


def get(name: str) -> tuple:
    """Return (handler, is_ui) for a tool name, or a no-op if unknown."""
    if name not in _REGISTRY:
        async def _unknown(_args):
            return {"error": f"Unknown tool: {name}"}
        return _unknown, False
    return _REGISTRY[name]


def get_step_label(name: str) -> tuple[str, str | None]:
    """Return (display label, icon) for the cl.Step UI."""
    label, icon = _STEP_LABELS.get(name, (name.replace("_", " ").title(), None))
    return label, icon
