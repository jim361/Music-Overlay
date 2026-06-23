from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any


DEFAULT_SETTINGS: dict[str, Any] = {
    "window": {
        "x": None,
        "y": None,
    },
    "media": {
        "selection_mode": "auto",
        "preferred_source": "spotify",
    },
    "overlay": {
        "language": "en",
        "show_album_art": True,
        "show_title": True,
        "show_details": True,
        "show_time": True,
        "show_progress_bar": True,
        "display_mode": "always",
        "auto_hide_seconds": 6,
        "background_opacity": 0.92,
        "font_family": "Segoe UI",
        "title_size": 14,
        "detail_size": 11,
        "meta_size": 10,
        "text_width": 440,
        "title_color": "#eaecef",
        "detail_color": "#929aa5",
        "meta_color": "#707a8a",
        "accent_color": "#FCD535",
    },
}


class SettingsManager:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or self.default_path()
        self.fallback_path = Path("settings.local.json")
        self._settings = self._load()

    @staticmethod
    def default_path() -> Path:
        base = os.getenv("LOCALAPPDATA")
        if base:
            return Path(base) / "Music Skin Overlay" / "settings.json"
        return Path("settings.local.json")

    def get(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._settings[key] = value
        self.save()

    def update_window_position(self, x: int, y: int) -> None:
        self._settings.setdefault("window", {})
        self._settings["window"]["x"] = x
        self._settings["window"]["y"] = y
        self.save()

    def update_media_selection(self, selection_mode: str, preferred_source: str) -> None:
        self._settings.setdefault("media", {})
        self._settings["media"]["selection_mode"] = selection_mode
        self._settings["media"]["preferred_source"] = preferred_source
        self.save()

    def update_overlay_option(self, key: str, value: Any) -> None:
        self._settings.setdefault("overlay", {})
        self._settings["overlay"][key] = value
        self.save()

    def reset_window_position(self) -> None:
        self._settings.setdefault("window", {})
        self._settings["window"]["x"] = None
        self._settings["window"]["y"] = None
        self.save()

    def window_position(self) -> tuple[int, int] | None:
        window = self._settings.get("window", {})
        x = window.get("x")
        y = window.get("y")
        if isinstance(x, int) and isinstance(y, int):
            return x, y
        return None

    def save(self) -> None:
        try:
            self._write_settings(self.path)
        except OSError:
            self.path = self.fallback_path
            self._write_settings(self.path)

    def _load(self) -> dict[str, Any]:
        settings = deepcopy(DEFAULT_SETTINGS)
        try:
            exists = self.path.exists()
        except OSError:
            self.path = self.fallback_path
            return settings

        if not exists:
            return settings

        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return settings

        return deep_merge(settings, loaded)

    def _write_settings(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self._settings, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result
