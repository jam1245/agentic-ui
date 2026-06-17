"""Iconify public API helpers — https://api.iconify.design"""

from __future__ import annotations

import urllib.parse

ICONIFY_API = "https://api.iconify.design"


def parse_icon_id(icon_id: str) -> tuple[str, str]:
    icon_id = icon_id.strip()
    if ":" in icon_id:
        prefix, name = icon_id.split(":", 1)
    elif "/" in icon_id:
        prefix, name = icon_id.split("/", 1)
    else:
        raise ValueError(f"icon_id must be 'prefix:name' or 'prefix/name', got: {icon_id!r}")
    if not prefix or not name:
        raise ValueError(f"Invalid icon_id: {icon_id!r}")
    return prefix, name


def icon_svg_url(prefix: str, name: str, height: int = 24, color: str | None = None) -> str:
    params: dict[str, str] = {"height": str(height)}
    if color:
        params["color"] = color
    qs = urllib.parse.urlencode(params)
    return f"{ICONIFY_API}/{prefix}/{name}.svg?{qs}"


def icon_png_url(prefix: str, name: str, height: int = 24) -> str:
    qs = urllib.parse.urlencode({"height": str(height)})
    return f"{ICONIFY_API}/{prefix}/{name}.png?{qs}"


def icon_entry(icon_id: str, height: int = 24, color: str | None = None) -> dict:
    prefix, name = parse_icon_id(icon_id)
    return {
        "icon_id": f"{prefix}:{name}",
        "prefix": prefix,
        "name": name,
        "svg_url": icon_svg_url(prefix, name, height=height, color=color),
        "png_url": icon_png_url(prefix, name, height=height),
    }
