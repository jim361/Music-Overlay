"""Probe Windows GSMTC media sessions.

This script is intentionally UI-free. Run it while Spotify, a browser, or a
PWA is playing media, then use the printed output to decide whether GSMTC is a
good enough data source for the overlay MVP.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import platform
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class MediaControls:
    play: bool | None
    pause: bool | None
    play_pause_toggle: bool | None
    next: bool | None
    previous: bool | None
    seek: bool | None


@dataclass
class MediaSnapshot:
    timestamp: str
    is_current_session: bool
    source_app_user_model_id: str | None
    title: str | None
    artist: str | None
    album_title: str | None
    album_artist: str | None
    playback_status: str | None
    position_seconds: float | None
    duration_seconds: float | None
    progress_percent: float | None
    controls: MediaControls
    has_thumbnail: bool
    thumbnail_saved_to: str | None
    error: str | None = None


def load_winrt_backend() -> dict[str, Any]:
    """Load either the winsdk or winrt package.

    The Python Windows Runtime ecosystem has used both import roots in the
    wild. Supporting both keeps this probe useful across machines.
    """

    try:
        from winsdk.windows.media.control import (  # type: ignore
            GlobalSystemMediaTransportControlsSessionManager,
        )

        try:
            from winsdk.windows.storage.streams import DataReader  # type: ignore
        except Exception:
            DataReader = None

        return {
            "name": "winsdk",
            "manager": GlobalSystemMediaTransportControlsSessionManager,
            "data_reader": DataReader,
        }
    except Exception as winsdk_error:
        try:
            from winrt.windows.media.control import (  # type: ignore
                GlobalSystemMediaTransportControlsSessionManager,
            )

            try:
                from winrt.windows.storage.streams import DataReader  # type: ignore
            except Exception:
                DataReader = None

            return {
                "name": "winrt",
                "manager": GlobalSystemMediaTransportControlsSessionManager,
                "data_reader": DataReader,
            }
        except Exception as winrt_error:
            raise RuntimeError(
                "Could not import a Windows Runtime backend. Install one with:\n"
                "  py -m pip install -r requirements-gsmtc.txt\n\n"
                f"winsdk import error: {winsdk_error}\n"
                f"winrt import error: {winrt_error}"
            ) from winrt_error


def get_member(obj: Any, *names: str, default: Any = None) -> Any:
    """Read a property or call a method using several possible API spellings."""

    for name in names:
        if hasattr(obj, name):
            value = getattr(obj, name)
            return value() if callable(value) else value
    return default


def get_callable(obj: Any, *names: str) -> Any:
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
        # Some bindings represent WinRT TimeSpan as 100 ns ticks.
        if abs(value) > 10_000_000:
            return float(value) / 10_000_000
        return float(value)
    return None


def format_seconds(value: float | None) -> str:
    if value is None:
        return "unknown"
    value = max(0, int(value))
    minutes, seconds = divmod(value, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def bool_or_none(obj: Any, *names: str) -> bool | None:
    value = get_member(obj, *names)
    if value is None:
        return None
    return bool(value)


async def maybe_save_thumbnail(
    thumbnail_ref: Any,
    data_reader_class: Any,
    output_dir: Path | None,
    label: str,
) -> str | None:
    if not output_dir or thumbnail_ref is None or data_reader_class is None:
        return None

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
        if load_async is None:
            return None
        await load_async(size)

        read_bytes = get_callable(reader, "read_bytes", "ReadBytes")
        if read_bytes is None:
            return None

        try:
            buffer = bytearray(size)
            raw = read_bytes(buffer)
            data = bytes(buffer) if raw is None or isinstance(raw, int) else bytes(raw)
        except TypeError:
            raw = read_bytes(size)
            if raw is None:
                return None
            data = bytes(raw)

        suffix = ".bin"
        if data.startswith(b"\x89PNG"):
            suffix = ".png"
        elif data.startswith(b"\xff\xd8"):
            suffix = ".jpg"
        elif data.startswith(b"RIFF") and b"WEBP" in data[:16]:
            suffix = ".webp"

        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{label}{suffix}"
        path.write_bytes(data)
        return str(path)
    except Exception as exc:
        return f"thumbnail save failed: {exc}"


async def snapshot_session(
    session: Any,
    *,
    is_current_session: bool,
    data_reader_class: Any,
    thumbnail_dir: Path | None,
    session_index: int,
) -> MediaSnapshot:
    now = datetime.now().isoformat(timespec="seconds")
    source_app = get_member(
        session,
        "source_app_user_model_id",
        "SourceAppUserModelId",
    )

    try:
        props_async = get_member(
            session,
            "try_get_media_properties_async",
            "TryGetMediaPropertiesAsync",
        )
        props = await props_async if props_async is not None else None
    except Exception as exc:
        props = None
        props_error = f"media properties failed: {exc}"
    else:
        props_error = None

    try:
        playback_info = get_member(session, "get_playback_info", "GetPlaybackInfo")
    except Exception as exc:
        playback_info = None
        playback_error = f"playback info failed: {exc}"
    else:
        playback_error = None

    try:
        timeline = get_member(
            session,
            "get_timeline_properties",
            "GetTimelineProperties",
        )
    except Exception as exc:
        timeline = None
        timeline_error = f"timeline failed: {exc}"
    else:
        timeline_error = None

    controls_obj = get_member(playback_info, "controls", "Controls") if playback_info else None
    controls = MediaControls(
        play=bool_or_none(controls_obj, "is_play_enabled", "IsPlayEnabled"),
        pause=bool_or_none(controls_obj, "is_pause_enabled", "IsPauseEnabled"),
        play_pause_toggle=bool_or_none(
            controls_obj,
            "is_play_pause_toggle_enabled",
            "IsPlayPauseToggleEnabled",
        ),
        next=bool_or_none(controls_obj, "is_next_enabled", "IsNextEnabled"),
        previous=bool_or_none(
            controls_obj,
            "is_previous_enabled",
            "IsPreviousEnabled",
        ),
        seek=bool_or_none(controls_obj, "is_playback_position_enabled", "IsPlaybackPositionEnabled"),
    )

    position = seconds_from_timespan(
        get_member(timeline, "position", "Position") if timeline else None
    )
    duration = seconds_from_timespan(
        get_member(timeline, "end_time", "EndTime") if timeline else None
    )
    progress = None
    if position is not None and duration and duration > 0:
        progress = round(max(0, min(100, position / duration * 100)), 2)

    title = get_member(props, "title", "Title") if props else None
    artist = get_member(props, "artist", "Artist") if props else None
    album_title = get_member(props, "album_title", "AlbumTitle") if props else None
    album_artist = get_member(props, "album_artist", "AlbumArtist") if props else None
    thumbnail = get_member(props, "thumbnail", "Thumbnail") if props else None
    thumbnail_saved_to = await maybe_save_thumbnail(
        thumbnail,
        data_reader_class,
        thumbnail_dir,
        f"session_{session_index}_thumbnail",
    )

    errors = [item for item in (props_error, playback_error, timeline_error) if item]

    return MediaSnapshot(
        timestamp=now,
        is_current_session=is_current_session,
        source_app_user_model_id=str(source_app) if source_app else None,
        title=str(title) if title else None,
        artist=str(artist) if artist else None,
        album_title=str(album_title) if album_title else None,
        album_artist=str(album_artist) if album_artist else None,
        playback_status=enum_to_name(
            get_member(playback_info, "playback_status", "PlaybackStatus")
            if playback_info
            else None
        ),
        position_seconds=position,
        duration_seconds=duration,
        progress_percent=progress,
        controls=controls,
        has_thumbnail=thumbnail is not None,
        thumbnail_saved_to=thumbnail_saved_to,
        error="; ".join(errors) if errors else None,
    )


def print_snapshot(snapshot: MediaSnapshot) -> None:
    marker = "CURRENT" if snapshot.is_current_session else "SESSION"
    print(f"[{snapshot.timestamp}] {marker}")
    print(f"  source:   {snapshot.source_app_user_model_id or 'unknown'}")
    print(f"  title:    {snapshot.title or 'unknown'}")
    print(f"  artist:   {snapshot.artist or 'unknown'}")
    print(f"  album:    {snapshot.album_title or 'unknown'}")
    print(f"  status:   {snapshot.playback_status or 'unknown'}")
    print(
        "  time:     "
        f"{format_seconds(snapshot.position_seconds)} / "
        f"{format_seconds(snapshot.duration_seconds)}"
        f" ({snapshot.progress_percent if snapshot.progress_percent is not None else 'unknown'}%)"
    )
    print(
        "  controls: "
        f"play={snapshot.controls.play}, "
        f"pause={snapshot.controls.pause}, "
        f"toggle={snapshot.controls.play_pause_toggle}, "
        f"prev={snapshot.controls.previous}, "
        f"next={snapshot.controls.next}, "
        f"seek={snapshot.controls.seek}"
    )
    print(f"  artwork:  {'yes' if snapshot.has_thumbnail else 'no'}")
    if snapshot.thumbnail_saved_to:
        print(f"  thumbnail: {snapshot.thumbnail_saved_to}")
    if snapshot.error:
        print(f"  error:    {snapshot.error}")
    print()


async def collect_snapshots(args: argparse.Namespace) -> list[MediaSnapshot]:
    backend = load_winrt_backend()
    manager_class = backend["manager"]
    request_async = get_member(manager_class, "request_async", "RequestAsync")
    if request_async is None:
        raise RuntimeError("GSMTC manager does not expose request_async.")

    manager = await request_async
    current = get_member(manager, "get_current_session", "GetCurrentSession")
    sessions = get_member(manager, "get_sessions", "GetSessions", default=[]) or []
    sessions = list(sessions)

    if args.current_only and current is not None:
        sessions = [current]
    elif current is not None and current not in sessions:
        sessions.insert(0, current)

    snapshots: list[MediaSnapshot] = []
    if not sessions:
        return snapshots

    thumbnail_dir = Path(args.thumbnail_dir) if args.save_thumbnail else None
    for index, session in enumerate(sessions):
        snapshots.append(
            await snapshot_session(
                session,
                is_current_session=session == current,
                data_reader_class=backend["data_reader"],
                thumbnail_dir=thumbnail_dir,
                session_index=index,
            )
        )
    return snapshots


async def run(args: argparse.Namespace) -> None:
    if platform.system() != "Windows":
        raise RuntimeError("GSMTC is only available on Windows.")

    while True:
        snapshots = await collect_snapshots(args)
        if args.json:
            print(json.dumps([asdict(item) for item in snapshots], ensure_ascii=False, indent=2))
        elif snapshots:
            for snapshot in snapshots:
                print_snapshot(snapshot)
        else:
            print("No active GSMTC media sessions found.")

        if not args.watch:
            break

        await asyncio.sleep(args.interval)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print current Windows GSMTC media session information."
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Keep polling instead of printing one snapshot.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Polling interval in seconds when --watch is used.",
    )
    parser.add_argument(
        "--current-only",
        action="store_true",
        help="Only print the current active media session.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON.",
    )
    parser.add_argument(
        "--save-thumbnail",
        action="store_true",
        help="Save thumbnail bytes when the session exposes artwork.",
    )
    parser.add_argument(
        "--thumbnail-dir",
        default="probe-output",
        help="Directory used by --save-thumbnail.",
    )
    return parser.parse_args()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    args = parse_args()
    try:
        asyncio.run(run(args))
        return 0
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
