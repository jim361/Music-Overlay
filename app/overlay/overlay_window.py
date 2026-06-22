from __future__ import annotations

import time
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import replace
from typing import Any, Callable

from PySide6.QtCore import QEvent, QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QColor, QContextMenuEvent, QKeyEvent, QMouseEvent, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QProgressBar,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.config.settings_manager import SettingsManager
from app.media.media_models import MediaSnapshot
from app.media.now_playing_provider import NowPlayingProvider
from app.media.session_selector import SourcePreference


class OverlayWindow(QWidget):
    snapshot_ready = Signal(object)
    snapshot_updated = Signal(object)

    def __init__(
        self,
        *,
        provider: NowPlayingProvider,
        theme: dict[str, Any],
        settings: SettingsManager,
    ) -> None:
        super().__init__()
        self.provider = provider
        self.theme = theme
        self.settings = settings
        self._drag_offset: QPoint | None = None
        self._last_track_key = None
        self._last_pixmap: QPixmap | None = None
        self._display_snapshot: MediaSnapshot | None = None
        self._display_snapshot_time = 0.0
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="media-provider")
        self._pending_snapshot: Future[MediaSnapshot] | None = None
        self.open_settings: Callable[[], None] | None = None

        self._setup_window()
        self._build_ui()
        self._apply_theme()
        self._restore_position()
        self.snapshot_ready.connect(self.update_snapshot)

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(1000)

        self.display_timer = QTimer(self)
        self.display_timer.timeout.connect(self.update_progress_display)
        self.display_timer.start(250)
        self.refresh()

    def _setup_window(self) -> None:
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setMouseTracking(True)
        self.setContextMenuPolicy(Qt.DefaultContextMenu)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self.card = QFrame(self)
        self.card.setObjectName("card")
        self.card.installEventFilter(self)
        root.addWidget(self.card)

        card_layout = QHBoxLayout(self.card)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(12)

        self.album_art = QLabel(self.card)
        self.album_art.setObjectName("albumArt")
        self.album_art.setFixedSize(76, 76)
        self.album_art.setScaledContents(True)
        self.album_art.installEventFilter(self)
        card_layout.addWidget(self.album_art)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(4)
        card_layout.addLayout(text_layout, stretch=1)

        self.title_label = QLabel(self.card)
        self.title_label.setObjectName("title")
        self.title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.title_label.setTextInteractionFlags(Qt.NoTextInteraction)
        self.title_label.installEventFilter(self)
        text_layout.addWidget(self.title_label)

        self.artist_label = QLabel(self.card)
        self.artist_label.setObjectName("artist")
        self.artist_label.installEventFilter(self)
        text_layout.addWidget(self.artist_label)

        self.album_label = QLabel(self.card)
        self.album_label.setObjectName("album")
        self.album_label.installEventFilter(self)
        text_layout.addWidget(self.album_label)

        self.bottom_widget = QWidget(self.card)
        self.bottom_widget.setObjectName("bottomRow")
        self.bottom_widget.installEventFilter(self)
        text_layout.addWidget(self.bottom_widget)

        bottom_layout = QHBoxLayout(self.bottom_widget)
        bottom_layout.setContentsMargins(0, 2, 0, 0)
        bottom_layout.setSpacing(8)

        self.progress = QProgressBar(self.card)
        self.progress.setObjectName("progress")
        self.progress.setRange(0, 1000)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(5)
        self.progress.installEventFilter(self)
        bottom_layout.addWidget(self.progress)

        self.time_label = QLabel(self.card)
        self.time_label.setObjectName("time")
        self.time_label.installEventFilter(self)
        bottom_layout.addWidget(self.time_label)

        bottom_layout.addStretch(1)

    def _apply_theme(self) -> None:
        window = self.theme["window"]
        style = self.theme["style"]
        layout = self.theme["layout"]

        self.resize(int(window["width"]), int(window["height"]))
        self.setWindowOpacity(1.0)
        self.album_art.setVisible(self.show_album_art_enabled())
        self.album_label.setVisible(bool(layout["show_album"]))
        self.progress.setMaximumWidth(int(layout.get("progress_width", 168)))
        self._sync_display_visibility()

        radius = int(window["radius"])
        font_family = self.overlay_text_option("font_family", style["font_family"])
        opacity = self.background_opacity()
        card_background = rgba_from_hex(
            style["background_color"],
            opacity,
        )
        card_border = rgba_from_hex(style["border_color"], opacity)
        title_size = self.overlay_int_option("title_size", int(style["title_size"]), 9, 32)
        detail_size = self.overlay_int_option("detail_size", int(style["artist_size"]), 8, 28)
        meta_size = self.overlay_int_option("meta_size", int(style["meta_size"]), 8, 24)
        title_color = self.overlay_color_option("title_color", style["text_color"])
        detail_color = self.overlay_color_option("detail_color", style["sub_text_color"])
        meta_color = self.overlay_color_option("meta_color", style["muted_text_color"])
        accent_color = self.overlay_color_option("accent_color", style["progress_color"])
        self.setStyleSheet(
            f"""
            QFrame#card {{
                background-color: {card_background};
                border-radius: {radius}px;
                border: 1px solid {card_border};
            }}
            QWidget#bottomRow {{
                background: transparent;
            }}
            QLabel#title {{
                color: {title_color};
                font-family: "{font_family}";
                font-size: {title_size}px;
                font-weight: 650;
            }}
            QLabel#artist, QLabel#album {{
                color: {detail_color};
                font-family: "{font_family}";
                font-size: {detail_size}px;
            }}
            QLabel#time {{
                color: {meta_color};
                font-family: "{font_family}";
                font-size: {meta_size}px;
            }}
            QProgressBar#progress {{
                background-color: {style["progress_background_color"]};
                border: 0;
                border-radius: 3px;
            }}
            QProgressBar#progress::chunk {{
                background-color: {accent_color};
                border-radius: 3px;
            }}
            """
        )

    def _restore_position(self) -> None:
        position = self.settings.window_position()
        if position:
            self.move(*position)
        else:
            self.move(80, 80)

    def refresh(self) -> None:
        if self._pending_snapshot and not self._pending_snapshot.done():
            return

        self._pending_snapshot = self._executor.submit(self.provider.get_snapshot)
        self._pending_snapshot.add_done_callback(self._handle_snapshot_result)

    def _handle_snapshot_result(self, future: Future[MediaSnapshot]) -> None:
        try:
            snapshot = future.result()
        except Exception as exc:
            snapshot = MediaSnapshot.error_snapshot(str(exc))
        self.snapshot_ready.emit(snapshot)

    def update_snapshot(self, snapshot: MediaSnapshot) -> None:
        snapshot = self.reconciled_snapshot(snapshot)
        title = snapshot.title or "No media playing"
        artist = snapshot.artist or "Unknown artist"
        album = snapshot.album or ""
        self._display_snapshot = snapshot
        self._display_snapshot_time = time.monotonic()

        self.title_label.setText(title)
        self.artist_label.setText(artist)
        self.album_label.setText(album)
        self.album_label.setVisible(bool(self.theme["layout"]["show_album"]) and bool(album))
        self.update_progress_display()
        self._sync_display_visibility()
        if self.show_album_art_enabled():
            self._update_album_art(snapshot)
        self.snapshot_updated.emit(snapshot)

    def reconciled_snapshot(self, snapshot: MediaSnapshot) -> MediaSnapshot:
        current_snapshot = self._display_snapshot
        if current_snapshot is None:
            return snapshot
        if current_snapshot.track_key != snapshot.track_key:
            return snapshot
        if not is_playing_status(snapshot.playback_status):
            return snapshot

        current_position = self.display_position_seconds(current_snapshot)
        incoming_position = snapshot.position_seconds
        if current_position is None or incoming_position is None:
            return snapshot

        lag = current_position - incoming_position
        if 0.0 <= lag <= 10.0:
            return replace(snapshot, position_seconds=current_position)
        return snapshot

    def update_progress_display(self) -> None:
        snapshot = self._display_snapshot
        if snapshot is None:
            return

        position = self.display_position_seconds(snapshot)
        duration = snapshot.duration_seconds
        self.time_label.setText(f"{format_time(position)} / {format_time(duration)}")

        if position is None or not duration or duration <= 0:
            self.progress.setValue(0)
            return

        progress = max(0.0, min(1.0, position / duration))
        self.progress.setValue(int(progress * self.progress.maximum()))

    def display_position_seconds(self, snapshot: MediaSnapshot) -> float | None:
        position = snapshot.position_seconds
        if position is None:
            return None

        duration = snapshot.duration_seconds
        if is_playing_status(snapshot.playback_status):
            position += max(0.0, time.monotonic() - self._display_snapshot_time)

        if duration and duration > 0:
            return max(0.0, min(duration, position))
        return max(0.0, position)

    def _update_album_art(self, snapshot: MediaSnapshot) -> None:
        if snapshot.track_key == self._last_track_key and self._last_pixmap:
            self.album_art.setPixmap(self._last_pixmap)
            return

        pixmap = QPixmap()
        if snapshot.thumbnail_bytes:
            pixmap.loadFromData(snapshot.thumbnail_bytes)

        if pixmap.isNull():
            pixmap = placeholder_pixmap(self.album_art.width(), self.album_art.height())

        self._last_track_key = snapshot.track_key
        self._last_pixmap = pixmap
        self.album_art.setPixmap(pixmap)

    def eventFilter(self, watched: object, event: QEvent) -> bool:
        if event.type() == QEvent.ContextMenu and isinstance(event, QContextMenuEvent):
            self._show_context_menu(event.globalPos())
            return True

        if event.type() == QEvent.MouseButtonPress and isinstance(event, QMouseEvent):
            if event.button() == Qt.LeftButton:
                self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                return True

        if event.type() == QEvent.MouseMove and isinstance(event, QMouseEvent):
            if self._drag_offset is not None:
                self.move(event.globalPosition().toPoint() - self._drag_offset)
                return True

        if event.type() == QEvent.MouseButtonRelease and isinstance(event, QMouseEvent):
            if self._drag_offset is not None:
                self._drag_offset = None
                self.settings.update_window_position(self.x(), self.y())
                return True

        return super().eventFilter(watched, event)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:  # type: ignore[override]
        self._show_context_menu(event.globalPos())

    def keyPressEvent(self, event: QKeyEvent) -> None:  # type: ignore[override]
        if event.key() == Qt.Key_Escape:
            QApplication.instance().quit()
            return
        if event.key() == Qt.Key_F5:
            self.refresh()
            return
        super().keyPressEvent(event)

    def _show_context_menu(self, position: QPoint) -> None:
        menu = QMenu(self)

        refresh_action = QAction("Refresh now", self)
        refresh_action.triggered.connect(self.refresh)
        menu.addAction(refresh_action)

        source_menu = menu.addMenu("Media source")
        for label, source in (
            ("Auto", "auto"),
            ("Spotify", "spotify"),
            ("Chrome", "chrome"),
            ("Edge", "edge"),
            ("Current Windows session", "current"),
        ):
            action = QAction(label, self)
            action.setCheckable(True)
            action.setChecked(self.current_source() == source)
            action.triggered.connect(lambda checked=False, value=source: self.set_source(value))
            source_menu.addAction(action)

        if self.open_settings is not None:
            settings_action = QAction("Settings...", self)
            settings_action.triggered.connect(self.open_settings)
            menu.addAction(settings_action)

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(lambda: QApplication.instance().quit())
        menu.addAction(quit_action)

        menu.exec(position)

    def current_source(self) -> str:
        media = self.settings.get("media", {})
        mode = media.get("selection_mode", "auto")
        source = media.get("preferred_source", "spotify")
        if mode == "auto":
            return "auto"
        if mode == "current":
            return "current"
        return source

    def set_source(self, source: str) -> None:
        if source == "auto":
            preference = SourcePreference(selection_mode="auto", preferred_source="spotify")
        elif source == "current":
            preference = SourcePreference(selection_mode="current", preferred_source="current")
        else:
            preference = SourcePreference(selection_mode="fixed", preferred_source=source)

        self.settings.update_media_selection(
            preference.selection_mode,
            preference.preferred_source,
        )

        if hasattr(self.provider, "preference"):
            setattr(self.provider, "preference", preference)
        if hasattr(self.provider, "_last_good"):
            setattr(self.provider, "_last_good", None)

        self._last_track_key = None
        self.refresh()

    def show_album_art_enabled(self) -> bool:
        layout = self.theme.get("layout", {})
        overlay = self.settings.get("overlay", {})
        return bool(layout.get("show_album_art", True)) and bool(
            overlay.get("show_album_art", True)
        )

    def set_show_album_art(self, enabled: bool) -> None:
        self.settings.update_overlay_option("show_album_art", bool(enabled))
        self.album_art.setVisible(self.show_album_art_enabled())
        if enabled:
            self._last_track_key = None
            self.refresh()

    def show_time_enabled(self) -> bool:
        overlay = self.settings.get("overlay", {})
        return bool(overlay.get("show_time", True))

    def set_show_time(self, enabled: bool) -> None:
        self.settings.update_overlay_option("show_time", bool(enabled))
        self._sync_display_visibility()

    def show_progress_bar_enabled(self) -> bool:
        layout = self.theme.get("layout", {})
        overlay = self.settings.get("overlay", {})
        return bool(layout.get("show_progress_bar", True)) and bool(
            overlay.get("show_progress_bar", True)
        )

    def set_show_progress_bar(self, enabled: bool) -> None:
        self.settings.update_overlay_option("show_progress_bar", bool(enabled))
        self._sync_display_visibility()

    def background_opacity(self) -> float:
        overlay = self.settings.get("overlay", {})
        value = float(overlay.get("background_opacity", 0.92))
        return max(0.0, min(1.0, value))

    def set_background_opacity(self, opacity: float) -> None:
        self.settings.update_overlay_option("background_opacity", max(0.0, min(1.0, opacity)))
        self._apply_theme()

    def overlay_int_option(self, key: str, fallback: int, minimum: int, maximum: int) -> int:
        overlay = self.settings.get("overlay", {})
        try:
            value = int(overlay.get(key, fallback))
        except (TypeError, ValueError):
            value = fallback
        return max(minimum, min(maximum, value))

    def overlay_color_option(self, key: str, fallback: str) -> str:
        overlay = self.settings.get("overlay", {})
        return normalized_hex_color(str(overlay.get(key, fallback)), fallback)

    def overlay_text_option(self, key: str, fallback: str) -> str:
        overlay = self.settings.get("overlay", {})
        value = str(overlay.get(key, fallback)).strip()
        return value or fallback

    def set_overlay_style_option(self, key: str, value: Any) -> None:
        self.settings.update_overlay_option(key, value)
        self._apply_theme()

    def _sync_display_visibility(self) -> None:
        show_progress = self.show_progress_bar_enabled()
        show_time = self.show_time_enabled()
        self.progress.setVisible(show_progress)
        self.time_label.setVisible(show_time)
        self.bottom_widget.setVisible(show_progress or show_time)

    def set_overlay_visible(self, visible: bool) -> None:
        if visible:
            self.show()
            self.raise_()
        else:
            self.hide()

    def apply_theme(self, theme: dict[str, Any]) -> None:
        self.theme = theme
        self._apply_theme()

    def reset_position(self) -> None:
        self.settings.reset_window_position()
        self.move(80, 80)
        self.settings.update_window_position(self.x(), self.y())

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self.settings.update_window_position(self.x(), self.y())
        self._executor.shutdown(wait=False, cancel_futures=True)
        super().closeEvent(event)


def format_time(value: float | None) -> str:
    if value is None:
        return "--:--"
    value = max(0, int(value))
    minutes, seconds = divmod(value, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def is_playing_status(status: str | None) -> bool:
    return bool(status and "playing" in status.casefold())


def placeholder_pixmap(width: int, height: int) -> QPixmap:
    pixmap = QPixmap(width, height)
    pixmap.fill(QColor("#1e2329"))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QColor("#707a8a"))
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "MSO")
    painter.end()
    return pixmap


def rgba_from_hex(color: str, opacity: float) -> str:
    color = normalized_hex_color(color, "#1e2329").lstrip("#")
    opacity = max(0.0, min(1.0, opacity))
    try:
        red = int(color[0:2], 16)
        green = int(color[2:4], 16)
        blue = int(color[4:6], 16)
    except ValueError:
        return f"rgba(30, 35, 41, {opacity:.2f})"

    return f"rgba({red}, {green}, {blue}, {opacity:.2f})"


def normalized_hex_color(value: str, fallback: str) -> str:
    color = value.strip()
    if len(color) == 7 and color.startswith("#"):
        try:
            int(color[1:], 16)
        except ValueError:
            return fallback
        return color.upper()
    return fallback
