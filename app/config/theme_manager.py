from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from app.utils.paths import resource_path


DEFAULT_THEME: dict[str, Any] = {
    "window": {
        "width": 380,
        "height": 104,
        "opacity": 1.0,
        "radius": 8,
    },
    "layout": {
        "show_album_art": True,
        "show_album": True,
        "show_progress_bar": True,
        "progress_width": 168,
        "text_width": 440,
    },
    "style": {
        "font_family": "Segoe UI",
        "title_size": 14,
        "artist_size": 11,
        "meta_size": 10,
        "background_color": "#1e2329",
        "border_color": "#2b3139",
        "text_color": "#eaecef",
        "sub_text_color": "#929aa5",
        "muted_text_color": "#707a8a",
        "progress_color": "#FCD535",
        "progress_background_color": "#2b3139",
    },
}


class ThemeManager:
    def __init__(self, theme_dir: Path | None = None) -> None:
        self.theme_dir = theme_dir or resource_path("themes")

    def load(self, name: str) -> dict[str, Any]:
        path = self.theme_dir / f"{name}.json"
        theme = deepcopy(DEFAULT_THEME)
        if not path.exists():
            return theme

        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return theme

        return deep_merge(theme, loaded)


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result
