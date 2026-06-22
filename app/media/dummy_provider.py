from __future__ import annotations

import math
import time

from app.media.media_models import MediaControls, MediaSnapshot


class DummyProvider:
    def __init__(self) -> None:
        self.started_at = time.monotonic()
        self.duration = 244.0

    def get_snapshot(self) -> MediaSnapshot:
        elapsed = time.monotonic() - self.started_at
        position = elapsed % self.duration
        status = "playing" if int(elapsed / 8) % 2 == 0 else "paused"
        artist = "Music Skin Overlay"
        title = "GSMTC Ready"
        album = "MVP Preview"

        # Small movement in dummy metadata makes update polling visible.
        if math.floor(elapsed / 16) % 2:
            title = "Custom Overlay Card"

        return MediaSnapshot(
            source_app="Dummy",
            title=title,
            artist=artist,
            album=album,
            playback_status=status,
            position_seconds=position,
            duration_seconds=self.duration,
            controls=MediaControls(
                play=status != "playing",
                pause=status == "playing",
                play_pause_toggle=True,
                next=True,
                previous=True,
                seek=True,
            ),
        )
