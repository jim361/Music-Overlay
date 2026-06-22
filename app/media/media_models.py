from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MediaControls:
    play: bool | None = None
    pause: bool | None = None
    play_pause_toggle: bool | None = None
    next: bool | None = None
    previous: bool | None = None
    seek: bool | None = None


@dataclass(frozen=True)
class MediaSnapshot:
    source_app: str | None = None
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    playback_status: str | None = None
    position_seconds: float | None = None
    duration_seconds: float | None = None
    thumbnail_bytes: bytes | None = None
    controls: MediaControls = MediaControls()
    is_current_session: bool = False
    error: str | None = None

    @property
    def progress_percent(self) -> float | None:
        if self.position_seconds is None or not self.duration_seconds:
            return None
        if self.duration_seconds <= 0:
            return None
        return max(0.0, min(100.0, self.position_seconds / self.duration_seconds * 100.0))

    @property
    def has_media(self) -> bool:
        return bool(self.title or self.artist or self.album)

    @property
    def track_key(self) -> tuple[str | None, str | None, str | None, str | None, float | None]:
        duration = round(self.duration_seconds or 0, 1) if self.duration_seconds else None
        return (self.source_app, self.title, self.artist, self.album, duration)

    @classmethod
    def empty(cls, message: str = "No media playing") -> MediaSnapshot:
        return cls(title=message, playback_status="unknown")

    @classmethod
    def error_snapshot(cls, message: str) -> MediaSnapshot:
        return cls(title="Media provider error", artist=message, playback_status="error", error=message)
