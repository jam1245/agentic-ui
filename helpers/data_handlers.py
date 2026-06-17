import os
import random
import json
import chainlit as cl

# --- Handlers ---

async def get_random_numbers(args: dict) -> dict:
    count = args.get("count", 5)
    min_val = args.get("min_value", 1)
    max_val = args.get("max_value", 100)
    numbers = [random.randint(min_val, max_val) for _ in range(count)]
    return {"numbers": numbers, "count": len(numbers)}


async def fetch_sample_dataframe(args: dict) -> dict:
    import pandas as pd

    dataset = args.get("dataset", "sales")

    if dataset == "users":
        data = {
            "Name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
            "Age": [28, 34, 22, 45, 31],
            "City": ["New York", "London", "Tokyo", "Paris", "Sydney"],
            "Score": [92, 85, 78, 96, 88],
        }
    elif dataset == "metrics":
        data = {
            "Metric": ["Latency (ms)", "Throughput (req/s)", "Error Rate (%)", "Uptime (%)"],
            "Value": [42, 1500, 0.3, 99.9],
            "Status": ["Good", "Excellent", "Good", "Excellent"],
        }
    else:  # sales
        data = {
            "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
            "Revenue": [12400, 15800, 11200, 17600, 21000, 18400],
            "Units": [124, 158, 112, 176, 210, 184],
            "Region": ["North", "South", "North", "East", "West", "South"],
        }

    df = pd.DataFrame(data)
    cl.user_session.set("latest_dataframe", df)
    return {
        "session_key": "latest_dataframe",
        "dataset": dataset,
        "columns": list(df.columns),
        "row_count": len(df),
    }


async def build_sample_plotly_figure(args: dict) -> dict:
    import plotly.graph_objects as go

    chart_type = args.get("chart_type", "bar")
    title = args.get("title", f"Sample {chart_type.title()} Chart")

    if chart_type == "bar":
        fig = go.Figure(go.Bar(
            x=["Q1", "Q2", "Q3", "Q4"],
            y=[23400, 31200, 28900, 36700],
            name="Revenue",
        ))
    elif chart_type == "line":
        fig = go.Figure(go.Scatter(
            x=["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
            y=[120, 145, 132, 178, 165, 210],
            mode="lines+markers",
            name="Active Users",
        ))
    elif chart_type == "scatter":
        fig = go.Figure(go.Scatter(
            x=[1.2, 2.4, 3.1, 4.5, 5.8, 6.2, 7.1],
            y=[2.1, 4.8, 3.9, 6.2, 5.5, 8.1, 7.4],
            mode="markers",
            name="Data Points",
        ))
    else:  # pie
        fig = go.Figure(go.Pie(
            labels=["North", "South", "East", "West"],
            values=[35, 25, 22, 18],
        ))

    fig.update_layout(title_text=title)
    fig_json = fig.to_json()
    cl.user_session.set("latest_plotly_figure", fig_json)
    return {
        "session_key": "latest_plotly_figure",
        "chart_type": chart_type,
        "title": title,
        "description": f"A {chart_type} chart titled '{title}' is ready to display.",
    }


async def get_sample_file_path(args: dict) -> dict:
    import csv
    import tempfile

    file_type = args.get("file_type", "txt")

    if file_type == "csv":
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv", prefix="sample_")
        writer = csv.writer(tmp)
        writer.writerow(["id", "name", "value"])
        writer.writerows([[1, "alpha", 100], [2, "beta", 200], [3, "gamma", 150]])
        tmp.close()
        path, name = tmp.name, "sample.csv"
    else:
        content = (
            "Sample File\n"
            "===========\n\n"
            "Generated in memory for the Chainlit demo — no repo file required.\n\n"
            "Demonstrates the cl.File element for chat downloads.\n"
        )
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".txt", prefix="sample_", mode="w", encoding="utf-8")
        tmp.write(content)
        tmp.close()
        path, name = tmp.name, "sample.txt"

    cl.user_session.set("latest_file_path", path)
    return {"session_key": "latest_file_path", "path": path, "file_type": file_type, "name": name}


async def fetch_iconify_icons(args: dict) -> dict:
    """Search Iconify or resolve a known icon id to CDN SVG/PNG URLs."""
    import httpx

    from .iconify_client import ICONIFY_API, icon_entry, parse_icon_id

    query = (args.get("query") or "").strip()
    icon_id = (args.get("icon_id") or "").strip()
    limit = min(max(int(args.get("limit", 8)), 1), 32)
    height = min(max(int(args.get("height", 24)), 8), 128)
    color = (args.get("color") or "").strip() or None
    prefixes = (args.get("prefixes") or "").strip() or None

    if icon_id:
        try:
            return {"icons": [icon_entry(icon_id, height=height, color=color)], "total": 1}
        except ValueError as e:
            return {"error": str(e)}

    if not query:
        return {"error": "Provide query (search) or icon_id (exact prefix:name)."}

    params: dict[str, str | int] = {"query": query, "limit": max(limit, 32)}
    if prefixes:
        params["prefixes"] = prefixes

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{ICONIFY_API}/search", params=params)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as e:
        return {"error": f"Iconify API request failed: {e}"}

    raw_icons = data.get("icons") or []
    icons = []
    for item in raw_icons[:limit]:
        try:
            icons.append(icon_entry(item, height=height, color=color))
        except ValueError:
            continue

    return {
        "query": query,
        "total": data.get("total", len(raw_icons)),
        "icons": icons,
        "usage_hint": (
            "In generated JSX use <img src={svg_url} alt=\"\" style={{ width: height, height }} /> "
            "or pass urls via props. Lucide is still preferred when a matching icon exists."
        ),
    }
