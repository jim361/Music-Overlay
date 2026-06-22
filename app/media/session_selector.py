from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from app.media.media_models import MediaSnapshot


@dataclass(frozen=True)
class SourcePreference:
    selection_mode: str = "auto"
    preferred_source: str = "spotify"


def select_snapshot(
    snapshots: Iterable[MediaSnapshot],
    preference: SourcePreference,
    last_good: MediaSnapshot | None = None,
) -> MediaSnapshot:
    items = [item for item in snapshots if item.has_media]
    if not items:
        return last_good or MediaSnapshot.empty()

    if preference.selection_mode == "current":
        current = first_current(items)
        return current or last_good or items[0]

    if preference.selection_mode == "fixed":
        fixed = first_matching(items, preference.preferred_source)
        return fixed or last_good or MediaSnapshot.empty(
            f"No {preference.preferred_source} media session"
        )

    preferred = first_matching(
        [item for item in items if item.playback_status == "playing"],
        preference.preferred_source,
    )
    if preferred:
        return preferred

    spotify = first_matching(
        [item for item in items if item.playback_status == "playing"],
        "spotify",
    )
    if spotify:
        return spotify

    playing = first_playing(items)
    if playing:
        return playing

    current = first_current(items)
    if current:
        return current

    return last_good or items[0]


def first_matching(items: Iterable[MediaSnapshot], source_name: str) -> MediaSnapshot | None:
    for item in items:
        if source_matches(item.source_app, source_name):
            return item
    return None


def first_playing(items: Iterable[MediaSnapshot]) -> MediaSnapshot | None:
    for item in items:
        if item.playback_status == "playing":
            return item
    return None


def first_current(items: Iterable[MediaSnapshot]) -> MediaSnapshot | None:
    for item in items:
        if item.is_current_session:
            return item
    return None


def source_matches(source_app: str | None, source_name: str) -> bool:
    if not source_app:
        return False

    source = source_app.casefold()
    name = source_name.casefold()

    if name == "current" or name == "auto":
        return True
    if name == "spotify":
        return "spotify" in source
    if name == "chrome":
        return "chrome" in source
    if name == "edge":
        return "edge" in source or "microsoftedge" in source

    return name in source
