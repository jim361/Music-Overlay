from __future__ import annotations

from typing import Protocol

from app.media.media_models import MediaSnapshot


class NowPlayingProvider(Protocol):
    def get_snapshot(self) -> MediaSnapshot:
        """Return the currently selected media snapshot."""
