from __future__ import annotations

import asyncio
from typing import Any

from app.media.media_models import MediaControls, MediaSnapshot
from app.media.session_selector import SourcePreference, select_snapshot


class GSMTCProvider:
    def __init__(self, preference: SourcePreference | None = None) -> None:
        self.preference = preference or SourcePreference()
        self._backend: dict[str, Any] | None = None
        self._last_good: MediaSnapshot | None = None

    def get_snapshot(self) -> MediaSnapshot:
        try:
            snapshots = asyncio.run(self._collect_snapshots())
        except Exception as exc:
            return MediaSnapshot.error_snapshot(str(exc))

        selected = select_snapshot(snapshots, self.preference, self._last_good)
        if selected.has_media and not selected.error:
            self._last_good = selected
        return selected

    async def _collect_snapshots(self) -> list[MediaSnapshot]:
        backend = self._load_backend()
        manager_class = backend["manager"]
        request_async = get_callable(manager_class, "request_async", "RequestAsync")
        if request_async is None:
            raise RuntimeError("GSMTC manager does not expose request_async.")

        manager = await request_async()
        current = get_member(manager, "get_current_session", "GetCurrentSession")
        sessions = list(get_member(manager, "get_sessions", "GetSessions", default=[]) or [])

        snapshots: list[MediaSnapshot] = []
        if current is not None:
            snapshots.append(
                await snapshot_session(
                    current,
                    data_reader_class=backend["data_reader"],
                    is_current_session=True,
                )
            )

        for session in sessions:
            snapshot = await snapshot_session(
                session,
                data_reader_class=backend["data_reader"],
                is_current_session=False,
            )
            if not has_same_identity(snapshot, snapshots):
                snapshots.append(snapshot)

        return snapshots

    def _load_backend(self) -> dict[str, Any]:
        if self._backend:
            return self._backend

        try:
            from winsdk.windows.media.control import (  # type: ignore
                GlobalSystemMediaTransportControlsSessionManager,
            )

            try:
                from winsdk.windows.storage.streams import DataReader  # type: ignore
            except Exception:
                DataReader = None

            self._backend = {
                "manager": GlobalSystemMediaTransportControlsSessionManager,
                "data_reader": DataReader,
            }
            return self._backend
        except Exception as exc:
            raise RuntimeError(
                "winsdk is not installed or GSMTC is unavailable. "
                "Run: py -3.12 -m pip install -r requirements.txt"
            ) from exc


async def snapshot_session(
    session: Any,
    *,
    data_reader_class: Any,
    is_current_session: bool,
) -> MediaSnapshot:
    source_app = get_member(
        session,
        "source_app_user_model_id",
        "SourceAppUserModelId",
    )

    props = None
    playback_info = None
    timeline = None
    thumbnail_bytes = None
    errors: list[str] = []

    try:
        props_async = get_callable(
            session,
            "try_get_media_properties_async",
            "TryGetMediaPropertiesAsync",
        )
        props = await props_async() if props_async else None
    except Exception as exc:
        errors.append(f"media properties failed: {exc}")

    try:
        playback_info = get_member(session, "get_playback_info", "GetPlaybackInfo")
    except Exception as exc:
        errors.append(f"playback info failed: {exc}")

    try:
        timeline = get_member(session, "get_timeline_properties", "GetTimelineProperties")
    except Exception as exc:
        errors.append(f"timeline failed: {exc}")

    thumbnail = get_member(props, "thumbnail", "Thumbnail") if props else None
    if thumbnail is not None and data_reader_class is not None:
        thumbnail_bytes = await read_thumbnail_bytes(thumbnail, data_reader_class)

    controls_obj = get_member(playback_info, "controls", "Controls") if playback_info else None
    position = seconds_from_timespan(
        get_member(timeline, "position", "Position") if timeline else None
    )
    duration = seconds_from_timespan(
        get_member(timeline, "end_time", "EndTime") if timeline else None
    )

    return MediaSnapshot(
        source_app=str(source_app) if source_app else None,
        title=string_or_none(get_member(props, "title", "Title") if props else None),
        artist=string_or_none(get_member(props, "artist", "Artist") if props else None),
        album=string_or_none(get_member(props, "album_title", "AlbumTitle") if props else None),
        playback_status=enum_to_name(
            get_member(playback_info, "playback_status", "PlaybackStatus")
            if playback_info
            else None
        ),
        position_seconds=position,
        duration_seconds=duration,
        thumbnail_bytes=thumbnail_bytes,
        controls=MediaControls(
            play=bool_or_none(controls_obj, "is_play_enabled", "IsPlayEnabled"),
            pause=bool_or_none(controls_obj, "is_pause_enabled", "IsPauseEnabled"),
            play_pause_toggle=bool_or_none(
                controls_obj,
                "is_play_pause_toggle_enabled",
                "IsPlayPauseToggleEnabled",
            ),
            next=bool_or_none(controls_obj, "is_next_enabled", "IsNextEnabled"),
            previous=bool_or_none(controls_obj, "is_previous_enabled", "IsPreviousEnabled"),
            seek=bool_or_none(
                controls_obj,
                "is_playback_position_enabled",
                "IsPlaybackPositionEnabled",
            ),
        ),
        is_current_session=is_current_session,
        error="; ".join(errors) if errors else None,
    )


async def read_thumbnail_bytes(thumbnail_ref: Any, data_reader_class: Any) -> bytes | None:
    try:
        open_read = get_callable(thumbnail_ref, "open_read_async", "OpenReadAsync")
        if open_read is None:
            return None

        stream = await open_read()
        size = int(get_member(stream, "size", "Size", default=0) or 0)
        if size <= 0:
            return None

        reader = data_reader_class(stream)
        load_async = get_callable(reader, "load_async", "LoadAsync")
        read_bytes = get_callable(reader, "read_bytes", "ReadBytes")
        if load_async is None or read_bytes is None:
            return None

        await load_async(size)

        try:
            buffer = bytearray(size)
            raw = read_bytes(buffer)
            return bytes(buffer) if raw is None or isinstance(raw, int) else bytes(raw)
        except TypeError:
            raw = read_bytes(size)
            return bytes(raw) if raw is not None else None
    except Exception:
        return None


def get_member(obj: Any, *names: str, default: Any = None) -> Any:
    if obj is None:
        return default
    for name in names:
        if hasattr(obj, name):
            value = getattr(obj, name)
            return value() if callable(value) else value
    return default


def get_callable(obj: Any, *names: str) -> Any:
    if obj is None:
        return None
    for name in names:
        if hasattr(obj, name):
            value = getattr(obj, name)
            if callable(value):
                return value
    return None


def enum_to_name(value: Any) -> str | None:
    if value is None:
        return None
    name = getattr(value, "name", None)
    if name:
        return str(name).lower()
    text = str(value)
    if "." in text:
        return text.rsplit(".", 1)[-1].lower()
    return text.lower()


def seconds_from_timespan(value: Any) -> float | None:
    if value is None:
        return None
    if hasattr(value, "total_seconds"):
        return float(value.total_seconds())
    if isinstance(value, (int, float)):
        if abs(value) > 10_000_000:
            return float(value) / 10_000_000
        return float(value)
    return None


def bool_or_none(obj: Any, *names: str) -> bool | None:
    value = get_member(obj, *names)
    if value is None:
        return None
    return bool(value)


def string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


def has_same_identity(snapshot: MediaSnapshot, existing: list[MediaSnapshot]) -> bool:
    return any(item.track_key == snapshot.track_key for item in existing)
