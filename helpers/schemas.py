import os


def _fn(name, description, properties, required=None):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required or [],
            },
        },
    }


# --- Data tools ---

GET_RANDOM_NUMBERS = _fn(
    "get_random_numbers",
    "Generate a list of random integers. Use when the user asks for random numbers or lottery picks.",
    {
        "count": {"type": "integer", "description": "How many numbers to generate (1-10)", "minimum": 1, "maximum": 10},
        "min_value": {"type": "integer", "description": "Minimum value (default 1)"},
        "max_value": {"type": "integer", "description": "Maximum value (default 100)"},
    },
    ["count"],
)

FETCH_ICONIFY_ICONS = _fn(
    "fetch_iconify_icons",
    (
        "Use before generate_custom_element_code for sprite-style subjects "
        "(dinosaur, cactus, cliff, characters) — NOT for Tetris, Snake, or other grid/block puzzle games "
        "(those use colored cells). Returns svg_url/png_url from https://api.iconify.design. "
        "Embed with <img src=\"...\" alt=\"\" style={{ width: 32, height: 32 }} />."
    ),
    {
        "query": {
            "type": "string",
            "description": "Search keywords (e.g. dinosaur, cliff, trophy). Ignored if icon_id is set.",
        },
        "icon_id": {
            "type": "string",
            "description": "Exact Iconify id as prefix:name (e.g. game-icons:dinosaur-rex). Skips search.",
        },
        "limit": {
            "type": "integer",
            "description": "Max icons to return (1-32, default 8)",
            "minimum": 1,
            "maximum": 32,
        },
        "height": {
            "type": "integer",
            "description": "Height in px for generated URLs (default 24)",
            "minimum": 8,
            "maximum": 128,
        },
        "color": {
            "type": "string",
            "description": "Optional SVG color (hex e.g. #ff0000 or CSS color)",
        },
        "prefixes": {
            "type": "string",
            "description": "Optional comma-separated icon set prefixes (e.g. game-icons,fluent-emoji-flat)",
        },
    },
)

FETCH_SAMPLE_DATAFRAME = _fn(
    "fetch_sample_dataframe",
    "Fetch a sample dataset as tabular data. Returns a session key for use with display_dataframe.",
    {
        "dataset": {
            "type": "string",
            "description": "Which sample dataset to load",
            "enum": ["sales", "users", "metrics"],
        },
    },
)

BUILD_SAMPLE_PLOTLY_FIGURE = _fn(
    "build_sample_plotly_figure",
    "Build a sample Plotly chart. Returns a session key for use with display_plotly.",
    {
        "chart_type": {
            "type": "string",
            "description": "Type of chart to generate",
            "enum": ["bar", "line", "scatter", "pie"],
        },
        "title": {"type": "string", "description": "Optional chart title"},
    },
    ["chart_type"],
)

GET_SAMPLE_FILE_PATH = _fn(
    "get_sample_file_path",
    "Create a sample downloadable file in a temp path (txt or csv). Returns a session key for display_file.",
    {
        "file_type": {
            "type": "string",
            "description": "Type of sample file",
            "enum": ["txt", "csv"],
        },
    },
)

# --- UI display tools ---

DISPLAY_ACTIONS = _fn(
    "display_actions",
    "Display 1-5 clickable choice buttons alongside the assistant message. Use whenever presenting options.",
    {
        "buttons": {
            "type": "array",
            "description": "List of 1-5 buttons",
            "minItems": 1,
            "maxItems": 5,
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Unique identifier for this button"},
                    "label": {"type": "string", "description": "Button display text"},
                    "icon": {"type": "string", "description": "Lucide icon name (e.g. 'sparkles', 'check')"},
                    "message": {"type": "string", "description": "Message sent when clicked (defaults to label)"},
                    "tooltip": {"type": "string", "description": "Hover tooltip text"},
                },
                "required": ["id", "label"],
            },
        }
    },
    ["buttons"],
)

DISPLAY_DATAFRAME = _fn(
    "display_dataframe",
    "Render a data table in the UI. Call fetch_sample_dataframe first to load data into session.",
    {
        "session_key": {"type": "string", "description": "Session key from fetch_sample_dataframe (default: latest_dataframe)"},
        "name": {"type": "string", "description": "Display name for the table"},
        "display": {"type": "string", "enum": ["inline", "side", "page"], "description": "How to display the element"},
    },
)

DISPLAY_PLOTLY = _fn(
    "display_plotly",
    "Render an interactive Plotly chart. Call build_sample_plotly_figure first to build the chart.",
    {
        "session_key": {"type": "string", "description": "Session key from build_sample_plotly_figure (default: latest_plotly_figure)"},
        "name": {"type": "string", "description": "Display name for the chart"},
        "display": {"type": "string", "enum": ["inline", "side", "page"], "description": "How to display the element"},
    },
)

DISPLAY_PYPLOT = _fn(
    "display_pyplot",
    "Render a static matplotlib chart. You provide the data directly in args.",
    {
        "chart_type": {"type": "string", "enum": ["bar", "line", "pie", "scatter"], "description": "Type of chart"},
        "title": {"type": "string", "description": "Chart title"},
        "x_labels": {"type": "array", "items": {"type": "string"}, "description": "X-axis labels or pie slice labels"},
        "y_values": {"type": "array", "items": {"type": "number"}, "description": "Y-axis values or pie slice sizes"},
        "x_label": {"type": "string", "description": "X-axis label"},
        "y_label": {"type": "string", "description": "Y-axis label"},
        "name": {"type": "string", "description": "Display name for the chart"},
        "display": {"type": "string", "enum": ["inline", "side", "page"]},
    },
    ["chart_type"],
)

DISPLAY_PDF = _fn(
    "display_pdf",
    "Show a PDF viewer in the chat. Provide a URL to any accessible PDF.",
    {
        "url": {"type": "string", "description": "URL of the PDF to display"},
        "name": {"type": "string", "description": "Display name shown to the user"},
        "display": {"type": "string", "enum": ["inline", "side", "page"]},
    },
)

DISPLAY_FILE = _fn(
    "display_file",
    "Attach a downloadable file. Call get_sample_file_path first, or provide inline text content.",
    {
        "session_key": {"type": "string", "description": "Session key from get_sample_file_path (default: latest_file_path)"},
        "name": {"type": "string", "description": "Filename shown to the user"},
        "text_content": {"type": "string", "description": "If no session_key, provide text content directly"},
    },
)

DISPLAY_CUSTOM_ELEMENT = _fn(
    "display_custom_element",
    (
        "Render an existing JSX file from public/elements/{name}.jsx. "
        "Tetris requests: always use name=TetrisGame (working built-in with keyboard). "
        "Other games: prefer generate_custom_element_code unless a curated file fits. "
        "Prefer display_stat_grid, display_record_editor, display_form when those tools fit."
    ),
    {
        "name": {"type": "string", "description": "Element name matching the JSX file (e.g. RatingWidget, ConsentForm)"},
        "props": {"type": "object", "description": "Props to pass to the JSX element"},
        "display": {"type": "string", "enum": ["inline", "side", "page"]},
    },
    ["name", "props"],
)

DISPLAY_TASKLIST = _fn(
    "display_tasklist",
    "Show a task progress list in the UI. Sent immediately as a standalone panel.",
    {
        "title": {"type": "string", "description": "Optional header label for the tasklist"},
        "tasks": {
            "type": "array",
            "description": "List of tasks to display",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Task description"},
                    "status": {"type": "string", "enum": ["ready", "running", "done", "failed"]},
                },
                "required": ["title", "status"],
            },
        },
    },
    ["tasks"],
)

DISPLAY_TEXT_ELEMENT = _fn(
    "display_text_element",
    "Show a text or markdown panel attached to the message.",
    {
        "name": {"type": "string", "description": "Reference name for the element"},
        "content": {"type": "string", "description": "Markdown or plain text content to display"},
        "display": {"type": "string", "enum": ["inline", "side", "page"]},
        "language": {"type": "string", "description": "Optional language hint for syntax highlighting"},
    },
    ["name", "content"],
)

DISPLAY_CODE_BLOCK = _fn(
    "display_code_block",
    (
        "Show a code snippet in a styled block with Copy and Download buttons. "
        "Long code collapses to max_lines with a fade + expand control. "
        "Use instead of pasting large fenced code in chat text."
    ),
    {
        "code": {"type": "string", "description": "Source code to display"},
        "content": {"type": "string", "description": "Alias for code"},
        "title": {"type": "string", "description": "Header label (default: filename or language)"},
        "language": {"type": "string", "description": "Language badge and download extension hint (python, ts, bash, etc.)"},
        "filename": {"type": "string", "description": "Download filename (e.g. script.py)"},
        "max_lines": {
            "type": "integer",
            "description": "Lines shown before collapse (default 12)",
            "minimum": 4,
            "maximum": 40,
        },
    },
    ["code"],
)

# --- UI ask tools ---

ASK_USER = _fn(
    "ask_user",
    "Pause and ask the user a free-text question. Blocks until the user replies.",
    {
        "content": {"type": "string", "description": "The question to display to the user"},
        "timeout": {"type": "integer", "description": "Seconds to wait before timing out (default 90)"},
    },
    ["content"],
)

ASK_FILE = _fn(
    "ask_file",
    "Pause and ask the user to upload a file. Blocks until a file is received.",
    {
        "content": {"type": "string", "description": "Prompt text shown above the upload button"},
        "accept": {
            "type": "array",
            "items": {"type": "string"},
            "description": "MIME types to accept, e.g. ['text/plain', 'application/pdf']",
        },
        "max_files": {"type": "integer", "description": "Maximum number of files (default 1)"},
        "timeout": {"type": "integer", "description": "Seconds to wait before timing out (default 90)"},
    },
    ["content"],
)

ASK_ACTION = _fn(
    "ask_action",
    "Pause and ask the user to pick one of a set of action buttons. Blocks until clicked.",
    {
        "content": {"type": "string", "description": "The prompt message shown to the user"},
        "actions": {
            "type": "array",
            "description": "List of action buttons",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Unique action identifier"},
                    "label": {"type": "string", "description": "Button display text"},
                    "icon": {"type": "string", "description": "Lucide icon name"},
                    "payload": {"type": "object", "description": "Data attached to the action"},
                },
                "required": ["name", "label"],
            },
        },
        "timeout": {"type": "integer", "description": "Seconds to wait (default 90)"},
    },
    ["content", "actions"],
)

ASK_ELEMENT = _fn(
    "ask_element",
    (
        "Pause and show a ConsentForm element for the user to fill out. Blocks until submitted. "
        "Provide fields as [{id, label, type (text/textarea/select/date), options?, value?, required?}]."
    ),
    {
        "content": {"type": "string", "description": "Prompt message shown above the form"},
        "title": {"type": "string", "description": "Form title"},
        "fields": {
            "type": "array",
            "description": "Form fields to display",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "label": {"type": "string"},
                    "type": {"type": "string", "enum": ["text", "textarea", "select", "date"]},
                    "options": {"type": "array", "items": {"type": "string"}},
                    "value": {"type": "string"},
                    "required": {"type": "boolean"},
                },
                "required": ["id", "label", "type"],
            },
        },
        "timeout": {"type": "integer", "description": "Seconds to wait (default 90)"},
    },
    ["content"],
)


DISPLAY_DROPDOWN = _fn(
    "display_dropdown",
    "Display a single-select dropdown for the user to pick one option. Submits immediately on confirm.",
    {
        "options": {
            "type": "array",
            "description": "List of options (strings or {value, label} objects)",
            "items": {"type": "string"},
        },
        "title": {"type": "string", "description": "Label shown above the dropdown"},
        "placeholder": {"type": "string", "description": "Placeholder text inside the select"},
    },
    ["options"],
)

DISPLAY_CHECKBOX = _fn(
    "display_checkbox",
    "Display a group of checkboxes for the user to pick one or more options.",
    {
        "options": {
            "type": "array",
            "description": "List of options (strings)",
            "items": {"type": "string"},
        },
        "title": {"type": "string", "description": "Label shown above the checkboxes"},
        "multiple": {"type": "boolean", "description": "Allow multiple selections (default true). Set false for single-select radio-style."},
        "min_selected": {"type": "integer", "description": "Minimum number of required selections"},
        "max_selected": {"type": "integer", "description": "Maximum number of allowed selections"},
    },
    ["options"],
)

DISPLAY_RANK = _fn(
    "display_rank",
    "Display a draggable ranked list so the user can reorder items by priority or preference.",
    {
        "items": {
            "type": "array",
            "description": "List of items to rank (strings)",
            "items": {"type": "string"},
        },
        "title": {"type": "string", "description": "Title shown above the list"},
        "instruction": {"type": "string", "description": "Instruction text (e.g. 'Drag to reorder. Top = highest priority.')"},
    },
    ["items"],
)

DISPLAY_CATEGORIES = _fn(
    "display_categories",
    (
        "Display 2-3 columns of draggable pills that the user can move between categories. "
        "Each column has a name and a list of starting items. "
        "Provide 2 columns (e.g. Yes/No) or 3 columns (e.g. High/Medium/Low priority)."
    ),
    {
        "columns": {
            "type": "array",
            "description": "2 or 3 columns, each with a name and optional starting items",
            "minItems": 2,
            "maxItems": 3,
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Column header label"},
                    "items": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Items starting in this column",
                    },
                },
                "required": ["name"],
            },
        },
        "title": {"type": "string", "description": "Title shown above the board"},
        "instruction": {"type": "string", "description": "Instruction text for the user"},
    },
    ["columns"],
)

DISPLAY_YEAR_CALENDAR = _fn(
    "display_year_calendar",
    (
        "Display a year calendar grid showing all 12 months. "
        "The user can click a month to send back the last day of that month (e.g. 2026-06-30). "
        "Use when the user wants to pick a month or needs a date in year-month format."
    ),
    {
        "year": {"type": "integer", "description": "The year to display (default: current year)"},
        "title": {"type": "string", "description": "Optional title for the calendar"},
    },
)


# --- Utility tools ---

RENAME_THREAD = _fn(
    "rename_thread",
    (
        "Rename the current conversation / thread to a descriptive title. "
        "Call this once at the start of a conversation when the user's intent is clear enough to summarize in a short title — "
        "e.g. after they ask about their goals, mention a review cycle, or start a check-in prep. "
        "Keep the name concise (3-6 words). Do NOT call repeatedly."
    ),
    {
        "name": {"type": "string", "description": "Short descriptive title for this conversation (e.g. 'Q3 Goal Review', 'Mid-Year Check-In Prep')"},
    },
    ["name"],
)


# --- Spreadsheet generation ---

GENERATE_XLSX = _fn(
    "generate_xlsx",
    (
        "Generate an Excel (.xlsx) spreadsheet and display a live grid preview with a download button. "
        "Supports multiple named sheets, each with column headers and data rows. "
        "Use when the user wants tabular data they can open in Excel: reports, trackers, exports, comparisons, schedules, etc. "
        "Cell values can be strings or numbers."
    ),
    {
        "filename": {"type": "string", "description": "Output filename without extension (e.g. 'goal-tracker-2026')"},
        "sheets": {
            "type": "array",
            "description": "One or more sheets in the workbook",
            "minItems": 1,
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Sheet tab name (e.g. 'Q1 Goals')"},
                    "headers": {
                        "type": "array",
                        "description": "Column header labels",
                        "items": {"type": "string"},
                    },
                    "rows": {
                        "type": "array",
                        "description": "Data rows; each row is an array of cell values (strings or numbers)",
                        "items": {"type": "array"},
                    },
                },
                "required": ["headers", "rows"],
            },
        },
    },
    ["sheets"],
)


# --- Gantt / visual timeline ---

DISPLAY_GANTT_TIMELINE = _fn(
    "display_gantt_timeline",
    (
        "Display a horizontal Gantt-style timeline where each item is a bar spanning from its start date to its end date. "
        "The X-axis starts at January 1 of the given year and extends to the latest end date. "
        "A vertical 'Today' line is shown automatically. "
        "Use when the user has a list of goals, projects, milestones, or tasks with target dates — any situation where you want to show duration and deadline visually side-by-side. "
        "Status values that control bar color: on_track (green), at_risk (amber), behind (red), complete (blue), draft (gray). "
        "Items without a status get distinct auto-assigned colors."
    ),
    {
        "title": {"type": "string", "description": "Optional heading above the chart"},
        "year": {"type": "integer", "description": "Year the timeline starts from (default: current year)"},
        "items": {
            "type": "array",
            "description": "Items to display as bars",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Item label shown in the left column"},
                    "end_date": {"type": "string", "description": "ISO date the bar ends (e.g. 2026-09-30)"},
                    "start_date": {"type": "string", "description": "ISO date the bar starts (default: Jan 1 of year)"},
                    "status": {
                        "type": "string",
                        "enum": ["on_track", "at_risk", "behind", "complete", "draft"],
                        "description": "Controls bar color",
                    },
                    "owner": {"type": "string", "description": "Optional secondary label (e.g. owner name)"},
                },
                "required": ["title", "end_date"],
            },
        },
    },
    ["items"],
)


# --- Document generation tools ---

GENERATE_WORD_DOC = _fn(
    "generate_word_doc",
    (
        "Generate a Word document (.docx) from structured content and display a live preview with a download button. "
        "Use when the user wants any written output they can download: reports, letters, memos, plans, assessments, summaries, agendas, etc. "
        "Each section has a heading and an array of content blocks. "
        "Block types: 'paragraph' (text field), 'bullets' (items array), 'table' (headers + rows arrays)."
    ),
    {
        "title": {"type": "string", "description": "Document title shown as the main heading"},
        "filename": {"type": "string", "description": "Output filename without extension (e.g. 'q3-performance-review')"},
        "sections": {
            "type": "array",
            "description": "Document sections",
            "items": {
                "type": "object",
                "properties": {
                    "heading": {"type": "string"},
                    "content": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string", "enum": ["paragraph", "bullets", "table"]},
                                "text": {"type": "string", "description": "For paragraph blocks"},
                                "items": {"type": "array", "items": {"type": "string"}, "description": "For bullet blocks"},
                                "headers": {"type": "array", "items": {"type": "string"}, "description": "For table blocks"},
                                "rows": {
                                    "type": "array",
                                    "items": {"type": "array", "items": {"type": "string"}},
                                    "description": "For table blocks",
                                },
                            },
                            "required": ["type"],
                        },
                    },
                },
                "required": ["heading"],
            },
        },
    },
    ["title", "sections"],
)


# --- HR / Performance tools ---

_DISPLAY_RECORD_PROPS = {
    "title": {"type": "string"},
    "subtitle": {"type": "string"},
    "description": {"type": "string"},
    "body": {"type": "string", "description": "Alias for description"},
    "due_date": {"type": "string"},
    "status": {"type": "string"},
    "status_options": {
        "type": "array",
        "description": "Custom status dropdown: strings or {value, label}",
        "items": {"type": ["string", "object"]},
    },
    "owner": {"type": "string"},
    "icon": {"type": "string", "description": "target, file, briefcase, flag, layers"},
    "items_label": {"type": "string", "description": "Label for checklist section (default: Items)"},
    "items": {
        "type": "array",
        "description": "Checklist rows: {text, complete} or strings",
        "items": {"type": ["string", "object"]},
    },
    "key_results": {"type": "array", "description": "Alias for items (goals)"},
    "fields": {
        "type": "array",
        "description": "Extra scalar fields when editing",
        "items": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "label": {"type": "string"},
                "type": {"type": "string", "enum": ["text", "textarea", "select", "date"]},
                "value": {"type": "string"},
                "options": {"type": "array", "items": {"type": ["string", "object"]}},
            },
            "required": ["id", "label"],
        },
    },
    "edit_mode": {"type": "boolean"},
    "editable": {"type": "boolean"},
    "save_label": {"type": "string"},
    "show_status": {"type": "boolean"},
    "allow_add_items": {"type": "boolean"},
}

DISPLAY_RECORD_EDITOR = _fn(
    "display_record_editor",
    (
        "Universal editable record card: title, status, due date, description, optional extra fields, "
        "and a checklist section (items). YOU define labels, status options, and rows for goals, "
        "projects, tickets, initiatives, etc. Prefer over generate_custom_element_code for structured editors."
    ),
    _DISPLAY_RECORD_PROPS,
    ["title"],
)

DISPLAY_GOAL_CARD = _fn(
    "display_goal_card",
    "Alias for display_record_editor with goal-friendly defaults (key results checklist).",
    _DISPLAY_RECORD_PROPS,
    ["title"],
)

DISPLAY_STAT_GRID = _fn(
    "display_stat_grid",
    (
        "KPI / metric tiles in a responsive grid. YOU supply label, value, optional delta, trend (up/down/neutral), "
        "suffix, and hint per stat. Use for dashboards, summaries, scorecards — not a chart."
    ),
    {
        "title": {"type": "string"},
        "subtitle": {"type": "string"},
        "columns": {"type": "integer", "description": "Grid columns 1-4 (default auto)"},
        "clickable": {"type": "boolean", "description": "Fire stat_grid_select when a tile is clicked"},
        "stats": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "label": {"type": "string"},
                    "value": {"type": "string", "description": "Displayed value (number or text)"},
                    "delta": {"type": "string", "description": "Change badge e.g. +12%"},
                    "delta_label": {"type": "string"},
                    "trend": {"type": "string", "enum": ["up", "down", "neutral"]},
                    "suffix": {"type": "string"},
                    "hint": {"type": "string"},
                    "icon": {"type": "string"},
                },
                "required": ["label", "value"],
            },
        },
    },
    ["stats"],
)

DISPLAY_PROGRESS_LIST = _fn(
    "display_progress_list",
    (
        "Rows with title, optional subtitle, progress 0-100, status or badge. "
        "Use for goals, projects, OKRs, courses, initiatives — YOU define items and labels."
    ),
    {
        "title": {"type": "string"},
        "subtitle": {"type": "string"},
        "clickable": {"type": "boolean", "description": "Click row to select (default true)"},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "subtitle": {"type": "string"},
                    "progress": {"type": "integer"},
                    "status": {"type": "string"},
                    "badge": {"type": "string", "description": "Override badge text"},
                    "bar_color": {"type": "string", "description": "Hex color for progress bar"},
                },
                "required": ["title"],
            },
        },
    },
    ["title", "items"],
)

DISPLAY_GOAL_PROGRESS = _fn(
    "display_goal_progress",
    "Deprecated: use display_progress_list with items[].",
    {
        "goals": {"type": "array", "items": {"type": "object"}},
        "title": {"type": "string"},
    },
    ["goals"],
)

DISPLAY_TREE = _fn(
    "display_tree",
    (
        "Collapsible nested tree. Use for OKRs, org structure, outlines, feature breakdowns. "
        "Nodes: id, title, status, badge, icon/level (company, team, individual, folder, item), children[]."
    ),
    {
        "title": {"type": "string"},
        "subtitle": {"type": "string"},
        "show_legend": {"type": "boolean"},
        "nodes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "status": {"type": "string"},
                    "badge": {"type": "string"},
                    "level": {"type": "string"},
                    "level_label": {"type": "string"},
                    "icon": {"type": "string"},
                    "children": {"type": "array"},
                },
                "required": ["title"],
            },
        },
    },
    ["nodes"],
)

DISPLAY_OKR_TREE = _fn(
    "display_okr_tree",
    "Deprecated: use display_tree.",
    {"nodes": {"type": "array", "items": {"type": "object"}}, "title": {"type": "string"}},
    ["nodes"],
)

# DISPLAY_FEEDBACK_PICKER archived — use DISPLAY_CARD_PICKER instead

DISPLAY_RATING_MATRIX = _fn(
    "display_rating_matrix",
    (
        "Show a multi-row 1-5 star rating matrix with optional comments. "
        "YOU define items (skills, criteria, dimensions, survey questions) — not a fixed competency list."
    ),
    {
        "title": {"type": "string"},
        "description": {"type": "string", "description": "Hint shown under title"},
        "include_comments": {"type": "boolean"},
        "max_rating": {"type": "integer"},
        "submit_label": {"type": "string"},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "label": {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["id", "label"],
            },
        },
    },
    ["title", "items"],
)

DISPLAY_COMPETENCY_RATER = _fn(
    "display_competency_rater",
    "Deprecated: use display_rating_matrix with items[].",
    {
        "competencies": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["id", "name"],
            },
        },
        "title": {"type": "string"},
        "include_comments": {"type": "boolean"},
    },
    ["competencies"],
)

# DISPLAY_FEEDBACK_CARD archived — use DISPLAY_SECTION_CARD instead
# DISPLAY_FEEDBACK_SUMMARY archived — use DISPLAY_PILL_BOARD instead

DISPLAY_SECTION_CARD = _fn(
    "display_section_card",
    (
        "Display a generic info card with a title, optional subtitle, header badges, key-value fields, "
        "and color-coded content sections. Use for feedback cards, goal summaries, review highlights, "
        "employee spotlights, or any structured card-style content. "
        "Section colors: green, amber, blue, purple, red, default. "
        "Badge styles: success, warning, danger, info, default."
    ),
    {
        "title": {"type": "string"},
        "subtitle": {"type": "string"},
        "header_badges": {
            "type": "array",
            "description": "Small badges shown in the header (e.g. status, type)",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "style": {"type": "string", "enum": ["success", "warning", "danger", "info", "default"]},
                },
                "required": ["label"],
            },
        },
        "header_fields": {
            "type": "array",
            "description": "Small key-value pairs shown in the header row",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "value": {"type": "string"},
                },
                "required": ["label", "value"],
            },
        },
        "sections": {
            "type": "array",
            "description": "Main content sections",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "color": {"type": "string", "enum": ["green", "amber", "blue", "purple", "red", "default"]},
                },
                "required": ["content"],
            },
        },
    },
    ["title"],
)

DISPLAY_PILL_BOARD = _fn(
    "display_pill_board",
    (
        "Display a board of labeled pill groups organized in 1-4 columns. "
        "Use for feedback themes, skill categories, topic clusters, pros/cons, strengths/development, or any tag-style summary. "
        "Each column has a name, a color, and a list of pill labels. "
        "Optional quotes are shown as blockquotes below the pills. "
        "Optional stats are shown as large numbers in the header. "
        "Column colors: green, amber, blue, purple, red, default."
    ),
    {
        "title": {"type": "string"},
        "subtitle": {"type": "string"},
        "columns": {
            "type": "array",
            "description": "1-4 columns of pill groups",
            "minItems": 1,
            "maxItems": 4,
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "items": {"type": "array", "items": {"type": "string"}},
                    "color": {"type": "string", "enum": ["green", "amber", "blue", "purple", "red", "default"]},
                },
                "required": ["name", "items"],
            },
        },
        "quotes": {"type": "array", "items": {"type": "string"}, "description": "Optional blockquote snippets"},
        "stats": {
            "type": "array",
            "description": "Optional header stats (e.g. total reviewers)",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "value": {"type": "string"},
                },
                "required": ["label", "value"],
            },
        },
    },
    ["columns"],
)

DISPLAY_CARD_PICKER = _fn(
    "display_card_picker",
    (
        "Display a grid of selectable cards for the user to pick one or more items. "
        "Use for selecting people (feedback requestees, colleagues, reviewers), choosing goals, "
        "picking skills, selecting from a list of options, or any multi-item selection scenario. "
        "Each item needs an id and name; subtitle and detail are optional secondary lines. "
        "max_selections controls how many can be picked (omit or use a high number for unlimited)."
    ),
    {
        "title": {"type": "string"},
        "items": {
            "type": "array",
            "description": "Items the user can pick from",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "subtitle": {"type": "string", "description": "Second line (e.g. job title, category)"},
                    "detail": {"type": "string", "description": "Third line (e.g. team, department)"},
                    "initials": {"type": "string", "description": "Override auto-generated initials"},
                },
                "required": ["id", "name"],
            },
        },
        "max_selections": {"type": "integer", "description": "Maximum number of items the user can select"},
        "submit_label": {"type": "string", "description": "Label for the confirm button (default: Confirm)"},
    },
    ["items"],
)

_FIELD_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "label": {"type": "string"},
        "placeholder": {"type": "string"},
        "help": {"type": "string", "description": "Hint below label"},
        "type": {
            "type": "string",
            "enum": [
                "text", "email", "number", "date", "textarea", "select", "radio",
                "checkbox", "switch", "multiselect", "heading", "divider",
            ],
            "description": "Default text. Use heading/divider for layout breaks.",
        },
        "required": {"type": "boolean"},
        "value": {"description": "Pre-fill: string, bool, or string[] for multiselect"},
        "max_chars": {"type": "integer"},
        "options": {
            "type": "array",
            "description": "For select, radio, multiselect — strings or {value, label}",
            "items": {"type": ["string", "object"]},
        },
        "rows": {"type": "integer", "description": "Textarea height"},
        "col_span": {"type": "integer", "description": "Grid columns to span (1-3)"},
        "full_width": {"type": "boolean", "description": "Span all columns in row/grid"},
        "min": {"type": "number"},
        "max": {"type": "number"},
    },
    "required": ["id", "label"],
}

DISPLAY_FORM = _fn(
    "display_form",
    (
        "Universal form (DynamicForm). YOU design title, layout, and every field for the user's task. "
        "Use fields[] for a flat list, or rows[] for explicit multi-column rows. "
        "Set columns (1-3) for a responsive grid on fields[]. "
        "Field types: text, email, number, date, textarea, select, radio, multiselect, checkbox, switch, heading, divider. "
        "Tailor labels/options/required flags — no fixed HR template."
    ),
    {
        "title": {"type": "string"},
        "subtitle": {"type": "string"},
        "description": {"type": "string", "description": "Instructions above fields"},
        "columns": {"type": "integer", "description": "Grid columns when using fields[] only (1-3, default 1)"},
        "rows": {
            "type": "array",
            "description": "Optional row layout: each row has columns (count) and fields (field objects or ids from fields[])",
            "items": {
                "type": "object",
                "properties": {
                    "columns": {"type": "integer", "description": "Columns in this row (default: field count)"},
                    "fields": {
                        "type": "array",
                        "description": "Field defs or string ids referencing fields[]",
                        "items": {"type": ["string", "object"]},
                    },
                },
            },
        },
        "due_date": {"type": "string"},
        "submit_label": {"type": "string"},
        "success_message": {"type": "string"},
        "show_draft": {"type": "boolean"},
        "compact": {"type": "boolean"},
        "max_chars": {"type": "integer"},
        "fields": {
            "type": "array",
            "description": "All field definitions (also reference by id in rows[])",
            "items": _FIELD_SCHEMA,
        },
    },
    ["title", "fields"],
)

# Back-compat alias — same handler, prefer display_form in new prompts
DISPLAY_ASSESSMENT_FORM = _fn(
    "display_assessment_form",
    "Deprecated: use display_form with tailored title and fields. Still accepts legacy sections[] shape.",
    {
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "placeholder": {"type": "string"},
                    "value": {"type": "string"},
                    "required": {"type": "boolean"},
                },
                "required": ["id", "title"],
            },
        },
        "title": {"type": "string"},
        "employee_name": {"type": "string"},
        "due_date": {"type": "string"},
    },
    ["sections"],
)

DISPLAY_TIER_PICKER = _fn(
    "display_tier_picker",
    (
        "Single-choice tier/level picker with optional comment. "
        "YOU supply tiers (labels, descriptions, values) for performance ratings, surveys, plans, risk levels, etc."
    ),
    {
        "tiers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "description": {"type": "string"},
                    "value": {"type": "string"},
                    "style": {"type": "string", "enum": ["emerald", "blue", "neutral", "amber", "red"]},
                },
                "required": ["label", "value"],
            },
        },
        "title": {"type": "string"},
        "subtitle": {"type": "string"},
        "require_comment": {"type": "boolean"},
        "comment_label": {"type": "string"},
        "comment_placeholder": {"type": "string"},
        "submit_label": {"type": "string"},
        "current_value": {"type": "string"},
    },
    ["title", "tiers"],
)

DISPLAY_PERFORMANCE_RATING = _fn(
    "display_performance_rating",
    "Deprecated: use display_tier_picker with tailored tiers and title.",
    {
        "tiers": {"type": "array", "items": {"type": "object"}},
        "title": {"type": "string"},
        "employee": {"type": "string"},
        "cycle": {"type": "string"},
        "require_justification": {"type": "boolean"},
        "current_rating": {"type": "string"},
    },
)

DISPLAY_EDITABLE_LIST = _fn(
    "display_editable_list",
    (
        "Editable reorderable list. preset=agenda (topics, notes, minutes) or preset=tasks (checkbox, text, notes, due date). "
        "Tailor title and initial rows to the user's request."
    ),
    {
        "preset": {"type": "string", "enum": ["agenda", "tasks", "custom"]},
        "title": {"type": "string"},
        "subtitle": {"type": "string"},
        "submit_label": {"type": "string"},
        "rows": {"type": "array", "items": {"type": "object"}},
        "topics": {"type": "array", "description": "Legacy alias for agenda rows"},
        "items": {"type": "array", "description": "Legacy alias for task rows"},
    },
    ["title"],
)

DISPLAY_CHECKIN_AGENDA = _fn(
    "display_checkin_agenda",
    "Deprecated: use display_editable_list with preset=agenda.",
    {
        "topics": {"type": "array", "items": {"type": "object"}},
        "title": {"type": "string"},
        "employee": {"type": "string"},
        "date": {"type": "string"},
        "check_in_type": {"type": "string"},
    },
)

DISPLAY_ACTION_ITEMS = _fn(
    "display_action_items",
    "Deprecated: use display_editable_list with preset=tasks.",
    {
        "items": {"type": "array", "items": {"type": "object"}},
        "title": {"type": "string"},
        "from_date": {"type": "string"},
    },
    ["items"],
)

DISPLAY_HIGHLIGHT_CARD = _fn(
    "display_highlight_card",
    (
        "Centered spotlight card: icon, headline, body, meta, optional CTA form. "
        "Use for awards, shout-outs, milestones, product launches — YOU set copy and CTA fields."
    ),
    {
        "headline": {"type": "string"},
        "subtitle": {"type": "string"},
        "body": {"type": "string"},
        "icon": {"type": "string", "enum": ["trophy", "star", "award", "zap", "heart", "medal", "sparkles"]},
        "accent_color": {"type": "string", "description": "Hex accent e.g. #f59e0b"},
        "meta": {"type": "array", "items": {"type": "object", "properties": {"label": {"type": "string"}, "value": {"type": "string"}}}},
        "show_cta": {"type": "boolean"},
        "cta": {
            "type": "object",
            "properties": {
                "label": {"type": "string"},
                "submit_label": {"type": "string"},
                "fields": {"type": "array", "items": {"type": "object"}},
            },
        },
        "success_message": {"type": "string"},
    },
    ["headline"],
)

DISPLAY_AWARD_CARD = _fn(
    "display_award_card",
    "Deprecated: use display_highlight_card (award_name→headline, citation→body).",
    {
        "award_name": {"type": "string"},
        "citation": {"type": "string"},
        "giver": {"type": "string"},
        "date": {"type": "string"},
        "recipient": {"type": "string"},
        "badge_icon": {"type": "string"},
        "show_nominate": {"type": "boolean"},
    },
    ["award_name", "citation"],
)

DISPLAY_TIMELINE = _fn(
    "display_timeline",
    (
        "Vertical event timeline. Each event: title, date, description, optional type "
        "(goal, feedback, checkin, award, milestone, other) or badge label."
    ),
    {
        "events": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "date": {"type": "string"},
                    "type": {"type": "string"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "badge": {"type": "string"},
                },
                "required": ["title"],
            },
        },
        "title": {"type": "string"},
        "subtitle": {"type": "string"},
    },
    ["events"],
)

DISPLAY_DATE_LIST = _fn(
    "display_date_list",
    "Cards showing days until due dates. Use for deadlines, milestones, renewals, any dated items.",
    {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "due_date": {"type": "string", "description": "ISO date"},
                    "badge": {"type": "string"},
                    "status": {"type": "string"},
                },
                "required": ["title", "due_date"],
            },
        },
        "title": {"type": "string"},
        "subtitle": {"type": "string"},
    },
    ["items"],
)

DISPLAY_DEADLINE_COUNTDOWN = _fn(
    "display_deadline_countdown",
    "Deprecated: use display_date_list.",
    {
        "deadlines": {"type": "array", "items": {"type": "object"}},
        "title": {"type": "string"},
    },
    ["deadlines"],
)


_JSX_GUIDE = """
Write a complete JSX file for a Chainlit custom element. Follow these rules exactly:

STRUCTURE:
  export default function {PascalCase}() { ... }
  File is saved as public/elements/_tmp_{PascalCase}_{uniqueId}.jsx (server appends a unique id each build).
  The component receives data via the GLOBAL `props` object — NOT function parameters.
  Example: const title = props.title || "Default";

ALLOWED UI IMPORTS (Chainlit shadcn — anything else will be rejected):
  @/components/ui/button
  @/components/ui/card  (+ CardContent, CardHeader, CardTitle, CardFooter, CardDescription)
  @/components/ui/badge
  @/components/ui/input
  @/components/ui/textarea
  @/components/ui/label
  @/components/ui/separator
  @/components/ui/checkbox
  @/components/ui/select  (+ SelectContent, SelectItem, SelectTrigger, SelectValue)
  @/components/ui/progress
  @/components/ui/tabs  (+ TabsList, TabsTrigger, TabsContent)
  @/components/ui/switch
  @/components/ui/avatar  (+ AvatarImage, AvatarFallback)
  @/components/ui/skeleton
  @/components/ui/tooltip  (+ TooltipProvider, TooltipTrigger, TooltipContent)
  @/components/ui/scroll-area  (+ ScrollBar)
  @/components/ui/table  (+ TableHeader, TableBody, TableRow, TableHead, TableCell)
  @/components/ui/dialog  (+ DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger)
  @/components/ui/dropdown-menu  (+ DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem)
  lucide-react  (named icons only)
  react — useState, useEffect, useRef, useMemo only

STYLING: Tailwind className is fine for layout and theme tokens (className="flex gap-2 rounded-lg border bg-card p-4").
  Use inline style for dynamic/state colors (selected, status) so classes are not purged.

LAYOUT: CSS grid/flex via className or inline style on <div> — no separate Grid component.
  Grids: gridTemplateColumns: "repeat(3, 1fr)", gap: 10, width: "100%", maxWidth: 360
  Grid cells: width: "100%", aspectRatio: "1" — NEVER fixed px width/height inside 1fr columns (causes huge gaps).

GLOBAL APIs (no import): props, callAction, updateElement, deleteElement, sendUserMessage

KEYBOARD (when the UI uses arrows or Space — paste into the same file, no imports):
  Spread {...focusBind} on root Card. NEVER raw window keydown without focus gating or Space breaks in chat.
  Use onFocus/onBlur + activeRef; only preventDefault while the card is focused.
  No cross-file imports — each .jsx must be self-contained.

GAMES / ANIMATION:
  - Implement full game logic in one file (movement, collision, scoring, game-over). No stubs or "// Logic to" comments.
  - Tailor mechanics and visuals to the user's request — different prompts must not share the same generic platform-runner layout.
  - Sprite runners (dinosaur, cactus obstacles): fetch_iconify_icons + <img src={svg_url} />.
  - Grid games (Tetris, Snake): colored div cells in a grid — full board width, render all piece cells with backgroundColor. No Iconify for tetrominoes.
  - Helpers used in useState(...) MUST be defined first: put function getPiece() { } above the component, or function declarations inside the component before useState. Never useState(getPiece()) when getPiece is const getPiece = () => below.
  - useState + useRef + useEffect; requestAnimationFrame or setInterval for ticks/gravity.

ICONS (required):
  NEVER use emojis or Unicode symbols anywhere in the UI.
  Prefer Lucide when a matching icon exists. For sprite subjects, call fetch_iconify_icons + <img src={svg_url} />. Tetris/grid games: colored cells only, not Iconify.
  ALWAYS use Lucide React icons when importing from lucide-react — import only icons that exist (wrong name => crash).
  INVALID (do not import): Pumpkin, Bat, Spider, Witch, Halloween, Christmas, Santa, etc.
  VALID examples: Star, Flame, Ghost, Skull, Moon, Sparkles, Heart, Check, X, Zap, Droplets,
    Leaf, Globe, Trophy, Award, User, Users, Calendar, Clock, Mail, Settings, Search.
  Map string keys to components; never render an undefined Icon:
    const ICONS = { ghost: Ghost, skull: Skull };
    const Icon = ICONS[props.iconKey] || Ghost;
    if (!Icon) return null;
    <Icon style={{ width: 24, height: 24 }} />

COLORS: Use Tailwind theme tokens (bg-primary, text-muted-foreground, border) for static UI.
  For state-driven colors (selected, status, progress), use inline style so values are not purged.

QUALITY (required — production UI, not prototypes):
  Wrap in Card + CardHeader + CardContent. Use boxShadow, borderRadius 8–12, padding 12–20.
  Build a real visual matching the request — not a single Input + Button unless that truly is the product.
  Build visuals that match the user's request (not generic placeholder labels).
  Never emoji. Never "Decoration 1" placeholders. Max 2 primary buttons.
  Interactive state: hover/selected styles via inline style, error messages inline (no alert()).

INTERACTIVITY (required — do not spam the LLM):
  Clicks, toggles, drags, and tile selects update React state ONLY — no callAction on each click.
  Always show a Done / Submit / Verify button. callAction ONLY when the user clicks that button:
  callAction({ name: "generated_element_action", payload: { done: true, action: "finished", element: "_tmp_{PascalCase}", ...allCollectedState } });
  (Server rewrites element to the final _tmp_{PascalCase}_{uniqueId} name on save.)
  Exception: single-step confirm buttons may use action: "verified" (or "submitted") with done: true.

SENDING DATA BACK TO THE LLM — always use this exact action name:
  callAction({ name: "generated_element_action", payload: { done: true, action: "finished", ...yourData } });

MINIMAL TEMPLATE:
  import { useState } from "react";
  import { Button } from "@/components/ui/button";
  export default function MyWidget() {
    const [value, setValue] = useState(0);
    const [finished, setFinished] = useState(false);
    const onDone = () => {
      setFinished(true);
      callAction({ name: "generated_element_action", payload: { done: true, action: "finished", value } });
    };
    if (finished) return <p style={{ padding: 12, fontSize: 13 }}>Saved.</p>;
    return (
      <div style={{ padding: 16, marginTop: 12, borderRadius: 8, border: "1px solid var(--border)" }}>
        <button type="button" onClick={() => setValue((v) => v + 1)}>Tap (+1)</button>
        <Button onClick={onDone} style={{ marginTop: 12 }}>Done</Button>
      </div>
    );
  }
"""

GENERATE_CUSTOM_ELEMENT_CODE = _fn(
    "generate_custom_element_code",
    (
        "Generate any custom interactive UI element from scratch. "
        "NOT for Tetris — use display_custom_element name=TetrisGame. "
        "Write JSX, save to public/elements/_tmp_{name}_{uniqueId}.jsx, and display immediately. "
        "Do NOT call display_custom_element after this — rendering is already done. "
        "Never use emojis in JSX; always use Lucide icons from lucide-react. "
        "UI must match the user's request with complete working logic (especially games — unique mechanics per prompt). "
        "Use for one-off interactives the display_* tools do not cover. "
        + _JSX_GUIDE
    ),
    {
        "element_name": {
            "type": "string",
            "description": "PascalCase component name with no spaces or hyphens (e.g. CaptchaWidget). Saved as public/elements/_tmp_{name}_{uniqueId}.jsx; CustomElement name matches that stem.",
        },
        "jsx_code": {
            "type": "string",
            "description": "Complete contents of the .jsx file, following the conventions in the tool description.",
        },
        "props": {
            "type": "object",
            "description": "JSON props passed to the component at render time. Must match what the JSX reads from the global `props` object.",
        },
    },
    ["element_name", "jsx_code"],
)

# When LLM_MODEL_JSX is set, the main model only plans; a dedicated model writes JSX.
GENERATE_CUSTOM_ELEMENT_CODE_PLANNER = _fn(
    "generate_custom_element_code",
    (
        "Request a custom interactive UI. The server generates full JSX using LLM_MODEL_JSX — "
        "you do NOT write the .jsx file. Provide element_name (PascalCase), props, and a clear "
        "requirements spec in jsx_code (features, layout, game rules, colors, controls). "
        "Do NOT use for Tetris — use display_custom_element name=TetrisGame instead. "
        "Call fetch_iconify_icons when sprite art is needed. Do NOT call display_custom_element after this."
    ),
    {
        "element_name": {
            "type": "string",
            "description": "PascalCase component name (e.g. DinosaurGame, TetrisGame).",
        },
        "jsx_code": {
            "type": "string",
            "description": "Requirements spec for the UI (NOT raw JSX). Server codegen fills the file.",
        },
        "props": {
            "type": "object",
            "description": "JSON props for the global `props` object in the element.",
        },
    },
    ["element_name", "jsx_code"],
)


def generate_custom_element_tool_schema():
    if os.environ.get("LLM_MODEL_JSX", "").strip():
        return GENERATE_CUSTOM_ELEMENT_CODE_PLANNER
    return GENERATE_CUSTOM_ELEMENT_CODE


DISPLAY_PLOTLY_CHART = _fn(
    "display_plotly_chart",
    (
        "Render an interactive Plotly chart using data you provide directly — no prior data-fetch call needed. "
        "Use this whenever the user's question can be answered with a chart and you already know the values "
        "(e.g. awards per year, goal progress history, comparisons). "
        "Preferred over build_sample_plotly_figure when you have real data to show. "
        "The chart appears below your message — do not duplicate the numbers in message text or say 'above'."
    ),
    {
        "title": {"type": "string", "description": "Chart title"},
        "chart_type": {
            "type": "string",
            "enum": ["bar", "line", "pie"],
            "description": "Chart type (default: bar)",
        },
        "x_labels": {
            "type": "array",
            "items": {"type": "string"},
            "description": "X-axis labels (categories, years, names, etc.)",
        },
        "y_values": {
            "type": "array",
            "items": {"type": "number"},
            "description": "Numeric values corresponding to each x_label",
        },
        "x_axis_label": {"type": "string", "description": "Optional x-axis title"},
        "y_axis_label": {"type": "string", "description": "Optional y-axis title"},
        "color": {"type": "string", "description": "Bar/line color as a hex code (e.g. #6366f1)"},
    },
    ["title", "x_labels", "y_values"],
)


ALL_TOOL_SCHEMAS = [
    GET_RANDOM_NUMBERS,
    FETCH_ICONIFY_ICONS,
    RENAME_THREAD,
    GENERATE_WORD_DOC,
    GENERATE_XLSX,
    DISPLAY_GANTT_TIMELINE,
    DISPLAY_PLOTLY_CHART,
    generate_custom_element_tool_schema(),
    FETCH_SAMPLE_DATAFRAME,
    BUILD_SAMPLE_PLOTLY_FIGURE,
    GET_SAMPLE_FILE_PATH,
    DISPLAY_ACTIONS,
    DISPLAY_DATAFRAME,
    DISPLAY_PLOTLY,
    DISPLAY_PYPLOT,
    DISPLAY_PDF,
    DISPLAY_FILE,
    DISPLAY_CUSTOM_ELEMENT,
    DISPLAY_TASKLIST,
    DISPLAY_TEXT_ELEMENT,
    DISPLAY_CODE_BLOCK,
    DISPLAY_DROPDOWN,
    DISPLAY_CHECKBOX,
    DISPLAY_RANK,
    DISPLAY_CATEGORIES,
    DISPLAY_YEAR_CALENDAR,
    DISPLAY_RECORD_EDITOR,
    DISPLAY_STAT_GRID,
    DISPLAY_GOAL_CARD,
    DISPLAY_PROGRESS_LIST,
    DISPLAY_GOAL_PROGRESS,
    DISPLAY_TREE,
    DISPLAY_OKR_TREE,
    # DISPLAY_FEEDBACK_PICKER — archived, use DISPLAY_CARD_PICKER
    DISPLAY_RATING_MATRIX,
    DISPLAY_COMPETENCY_RATER,
    # DISPLAY_FEEDBACK_CARD — archived, use DISPLAY_SECTION_CARD
    # DISPLAY_FEEDBACK_SUMMARY — archived, use DISPLAY_PILL_BOARD
    DISPLAY_SECTION_CARD,
    DISPLAY_PILL_BOARD,
    DISPLAY_CARD_PICKER,
    DISPLAY_FORM,
    DISPLAY_ASSESSMENT_FORM,
    DISPLAY_TIER_PICKER,
    DISPLAY_PERFORMANCE_RATING,
    DISPLAY_EDITABLE_LIST,
    DISPLAY_CHECKIN_AGENDA,
    DISPLAY_ACTION_ITEMS,
    DISPLAY_HIGHLIGHT_CARD,
    DISPLAY_AWARD_CARD,
    DISPLAY_TIMELINE,
    DISPLAY_DATE_LIST,
    DISPLAY_DEADLINE_COUNTDOWN,
    ASK_USER,
    ASK_FILE,
    ASK_ACTION,
    ASK_ELEMENT,
]
