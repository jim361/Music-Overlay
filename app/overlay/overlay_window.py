from __future__ import annotations

import time
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import replace
from typing import Any, Callable

from PySide6.QtCore import QEvent, QPoint, QSize, Qt, QTimer, Signal
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
from app.localization import normalize_language, translate
from app.media.media_models import MediaSnapshot
from app.media.now_playing_provider import NowPlayingProvider
from app.media.session_selector import SourcePreference


DEFAULT_ALBUM_ART_SIZE = 76
MAX_ALBUM_ART_SIZE = 180
CARD_MARGIN = 12
CARD_SPACING = 12
DEFAULT_TEXT_WIDTH = 440
MIN_TEXT_WIDTH = 180
MAX_TEXT_WIDTH = 760
DEFAULT_AUTO_HIDE_SECONDS = 6
MIN_AUTO_HIDE_SECONDS = 1
MAX_AUTO_HIDE_SECONDS = 60
TEXT_ROW_SPACING = 4


class ElidedLabel(QLabel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._full_text = ""

    def setText(self, text: str) -> None:  # type: ignore[override]
        self._full_text = text
        self.refresh_elision()

    def full_text(self) -> str:
        return self._full_text

    def sizeHint(self) -> QSize:  # type: ignore[override]
        hint = super().sizeHint()
        return QSize(0, hint.height())

    def minimumSizeHint(self) -> QSize:  # type: ignore[override]
        hint = super().minimumSizeHint()
        return QSize(0, hint.height())

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self.refresh_elision()

    def changeEvent(self, event) -> None:  # type: ignore[override]
        super().changeEvent(event)
        if event.type() in (QEvent.FontChange, QEvent.StyleChange):
            self.refresh_elision()

    def refresh_elision(self) -> None:
        width = self.contentsRect().width()
        text = self._full_text
        if width > 0:
            text = self.fontMetrics().elidedText(self._full_text, Qt.ElideRight, width)

        if QLabel.text(self) != text:
            QLabel.setText(self, text)
        self.setToolTip(self._full_text if text != self._full_text else "")


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
        self._album_art_size = DEFAULT_ALBUM_ART_SIZE
        self._last_revealed_track_key = None
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

        self.auto_hide_timer = QTimer(self)
        self.auto_hide_timer.setSingleShot(True)
        self.auto_hide_timer.timeout.connect(self.hide)
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
        card_layout.setContentsMargins(CARD_MARGIN, CARD_MARGIN, CARD_MARGIN, CARD_MARGIN)
        card_layout.setSpacing(CARD_SPACING)

        self.album_art = QLabel(self.card)
        self.album_art.setObjectName("albumArt")
        self.album_art.setFixedSize(DEFAULT_ALBUM_ART_SIZE, DEFAULT_ALBUM_ART_SIZE)
        self.album_art.setScaledContents(True)
        self.album_art.installEventFilter(self)
        card_layout.addWidget(self.album_art)

        self.text_panel = QWidget(self.card)
        self.text_panel.setObjectName("textPanel")
        self.text_panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.text_panel.installEventFilter(self)

        text_layout = QVBoxLayout(self.text_panel)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(4)
        card_layout.addWidget(self.text_panel, stretch=0)

        self.title_label = ElidedLabel(self.card)
        self.title_label.setObjectName("title")
        self.title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.title_label.setTextInteractionFlags(Qt.NoTextInteraction)
        self.title_label.installEventFilter(self)
        text_layout.addWidget(self.title_label)

        self.artist_label = ElidedLabel(self.card)
        self.artist_label.setObjectName("artist")
        self.artist_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.artist_label.installEventFilter(self)
        text_layout.addWidget(self.artist_label)

        self.album_label = ElidedLabel(self.card)
        self.album_label.setObjectName("album")
        self.album_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
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
        self._update_album_art_size(refresh_pixmap=True)
        self._resize_to_content()

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
        previous_snapshot = self._display_snapshot
        should_reveal = self.should_reveal_for_snapshot(previous_snapshot, snapshot)
        title = snapshot.title or "No media playing"
        artist = snapshot.artist or "Unknown artist"
        album = snapshot.album or ""
        self._display_snapshot = snapshot
        self._display_snapshot_time = time.monotonic()

        self.title_label.setText(title)
        self.artist_label.setText(artist)
        self.album_label.setText(album)
        self.update_progress_display()
        self._sync_display_visibility()
        self._update_album_art_size()
        self._resize_to_content()
        if self.show_album_art_enabled():
            self._update_album_art(snapshot)
        if should_reveal:
            self.reveal_temporarily()
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
        language = self.language()

        refresh_action = QAction(translate("refresh_now", language), self)
        refresh_action.triggered.connect(self.refresh)
        menu.addAction(refresh_action)

        source_menu = menu.addMenu(translate("media_source", language))
        for label_key, source in (
            ("source_auto", "auto"),
            ("source_spotify", "spotify"),
            ("source_chrome", "chrome"),
            ("source_edge", "edge"),
            ("source_current", "current"),
        ):
            action = QAction(translate(label_key, language), self)
            action.setCheckable(True)
            action.setChecked(self.current_source() == source)
            action.triggered.connect(lambda checked=False, value=source: self.set_source(value))
            source_menu.addAction(action)

        if self.open_settings is not None:
            settings_action = QAction(translate("settings", language), self)
            settings_action.triggered.connect(self.open_settings)
            menu.addAction(settings_action)

        quit_action = QAction(translate("quit", language), self)
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

    def language(self) -> str:
        overlay = self.settings.get("overlay", {})
        return normalize_language(str(overlay.get("language", "en")))

    def set_language(self, language: str) -> None:
        self.settings.update_overlay_option("language", normalize_language(language))

    def display_mode(self) -> str:
        overlay = self.settings.get("overlay", {})
        mode = str(overlay.get("display_mode", "always"))
        if mode not in {"always", "on_change"}:
            return "always"
        return mode

    def set_display_mode(self, mode: str) -> None:
        mode = mode if mode in {"always", "on_change"} else "always"
        self.settings.update_overlay_option("display_mode", mode)
        self.apply_display_mode()

    def auto_hide_seconds(self) -> int:
        overlay = self.settings.get("overlay", {})
        try:
            value = int(overlay.get("auto_hide_seconds", DEFAULT_AUTO_HIDE_SECONDS))
        except (TypeError, ValueError):
            value = DEFAULT_AUTO_HIDE_SECONDS
        return max(MIN_AUTO_HIDE_SECONDS, min(MAX_AUTO_HIDE_SECONDS, value))

    def set_auto_hide_seconds(self, seconds: int) -> None:
        value = max(MIN_AUTO_HIDE_SECONDS, min(MAX_AUTO_HIDE_SECONDS, int(seconds)))
        self.settings.update_overlay_option("auto_hide_seconds", value)
        if self.display_mode() == "on_change" and self.isVisible():
            self.reveal_temporarily()

    def apply_initial_visibility(self) -> None:
        if self.display_mode() == "on_change":
            self.hide()
        else:
            self.show()

    def apply_display_mode(self) -> None:
        self.auto_hide_timer.stop()
        if self.display_mode() == "always":
            self.show()
            self.raise_()
        else:
            self.hide()

    def should_reveal_for_snapshot(
        self,
        previous: MediaSnapshot | None,
        snapshot: MediaSnapshot,
    ) -> bool:
        if self.display_mode() != "on_change":
            return False
        if not is_revealable_media(snapshot):
            return False

        track_key = snapshot.track_key
        previous_key = previous.track_key if previous and is_revealable_media(previous) else None
        if track_key == previous_key:
            return False
        if track_key == self._last_revealed_track_key:
            return False

        self._last_revealed_track_key = track_key
        return True

    def reveal_temporarily(self) -> None:
        self.show()
        self.raise_()
        self.auto_hide_timer.start(self.auto_hide_seconds() * 1000)

    def show_album_art_enabled(self) -> bool:
        layout = self.theme.get("layout", {})
        overlay = self.settings.get("overlay", {})
        return bool(layout.get("show_album_art", True)) and bool(
            overlay.get("show_album_art", True)
        )

    def set_show_album_art(self, enabled: bool) -> None:
        self.settings.update_overlay_option("show_album_art", bool(enabled))
        self._sync_display_visibility()
        self._update_album_art_size(refresh_pixmap=enabled)
        self._resize_to_content()
        if enabled:
            self._last_track_key = None
            self.refresh()

    def show_title_enabled(self) -> bool:
        overlay = self.settings.get("overlay", {})
        return bool(overlay.get("show_title", True))

    def set_show_title(self, enabled: bool) -> None:
        self.settings.update_overlay_option("show_title", bool(enabled))
        self._sync_display_visibility()
        self._update_album_art_size(refresh_pixmap=True)
        self._resize_to_content()

    def show_details_enabled(self) -> bool:
        overlay = self.settings.get("overlay", {})
        return bool(overlay.get("show_details", True))

    def set_show_details(self, enabled: bool) -> None:
        self.settings.update_overlay_option("show_details", bool(enabled))
        self._sync_display_visibility()
        self._update_album_art_size(refresh_pixmap=True)
        self._resize_to_content()

    def show_time_enabled(self) -> bool:
        overlay = self.settings.get("overlay", {})
        return bool(overlay.get("show_time", True))

    def set_show_time(self, enabled: bool) -> None:
        self.settings.update_overlay_option("show_time", bool(enabled))
        self._sync_display_visibility()
        self._update_album_art_size(refresh_pixmap=True)
        self._resize_to_content()

    def show_progress_bar_enabled(self) -> bool:
        layout = self.theme.get("layout", {})
        overlay = self.settings.get("overlay", {})
        return bool(layout.get("show_progress_bar", True)) and bool(
            overlay.get("show_progress_bar", True)
        )

    def set_show_progress_bar(self, enabled: bool) -> None:
        self.settings.update_overlay_option("show_progress_bar", bool(enabled))
        self._sync_display_visibility()
        self._update_album_art_size(refresh_pixmap=True)
        self._resize_to_content()

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
        show_title = self.show_title_enabled()
        show_details = self.show_details_enabled()
        show_album_art = self.show_album_art_enabled()
        show_album = (
            show_details
            and bool(self.theme.get("layout", {}).get("show_album", True))
            and bool(self.album_label.full_text())
        )
        self.album_art.setVisible(show_album_art)
        self.title_label.setVisible(show_title)
        self.artist_label.setVisible(show_details)
        self.album_label.setVisible(show_album)
        self.progress.setVisible(show_progress)
        self.time_label.setVisible(show_time)
        self.bottom_widget.setVisible(show_progress or show_time)
        self.text_panel.setVisible(show_title or show_details or show_album or show_progress or show_time)

    def _refresh_elided_labels(self) -> None:
        self.title_label.refresh_elision()
        self.artist_label.refresh_elision()
        self.album_label.refresh_elision()

    def _apply_text_width(self, width: int) -> None:
        self.text_panel.setFixedWidth(width)
        for widget in (
            self.title_label,
            self.artist_label,
            self.album_label,
            self.bottom_widget,
        ):
            widget.setFixedWidth(width)
        self._refresh_elided_labels()

    def _update_album_art_size(self, *, refresh_pixmap: bool = False) -> None:
        if not self.show_album_art_enabled():
            return

        target_size = self._text_stack_height()
        target_size = max(DEFAULT_ALBUM_ART_SIZE, min(MAX_ALBUM_ART_SIZE, target_size))
        if target_size == self._album_art_size:
            return

        self._album_art_size = target_size
        self.album_art.setFixedSize(target_size, target_size)
        self._last_track_key = None
        if refresh_pixmap and self._display_snapshot is not None:
            self._update_album_art(self._display_snapshot)

    def _text_stack_height(self) -> int:
        visible_rows = [
            self.title_label,
            self.artist_label,
            self.album_label,
            self.bottom_widget,
        ]
        heights = [
            max(widget.sizeHint().height(), widget.minimumSizeHint().height())
            for widget in visible_rows
            if not widget.isHidden()
        ]
        if not heights:
            return DEFAULT_ALBUM_ART_SIZE
        return sum(heights) + (len(heights) - 1) * TEXT_ROW_SPACING

    def _resize_to_content(self) -> None:
        text_width = self._target_text_width()
        target_width = self._target_window_width(text_width)
        self.setFixedWidth(target_width)
        self.card.setFixedWidth(target_width)
        self._apply_text_width(text_width)
        self.layout().activate()
        minimum_height = int(self.theme["window"]["height"])
        target_height = max(minimum_height, self.sizeHint().height())
        self.resize(target_width, target_height)

    def _target_window_width(self, text_width: int) -> int:
        art_width = self._album_art_size if self.show_album_art_enabled() else 0
        has_text = self.text_panel.isVisible()
        spacing = CARD_SPACING if art_width and has_text else 0
        text_width = text_width if has_text else 0
        return CARD_MARGIN * 2 + art_width + spacing + text_width

    def _target_text_width(self) -> int:
        layout = self.theme.get("layout", {})
        fallback = self._theme_text_width(layout)
        overlay = self.settings.get("overlay", {})
        try:
            value = int(overlay.get("text_width", fallback))
        except (TypeError, ValueError):
            value = fallback
        return max(MIN_TEXT_WIDTH, min(MAX_TEXT_WIDTH, value))

    def _theme_text_width(self, layout: dict[str, Any]) -> int:
        fallback = self._fallback_text_width()
        try:
            value = int(layout.get("text_width", fallback))
        except (TypeError, ValueError):
            value = fallback
        return max(MIN_TEXT_WIDTH, min(MAX_TEXT_WIDTH, value))

    def _fallback_text_width(self) -> int:
        try:
            window_width = int(self.theme["window"]["width"])
        except (KeyError, TypeError, ValueError):
            return DEFAULT_TEXT_WIDTH

        art_width = DEFAULT_ALBUM_ART_SIZE if self.show_album_art_enabled() else 0
        spacing = CARD_SPACING if art_width else 0
        available = window_width - CARD_MARGIN * 2 - art_width - spacing
        return max(MIN_TEXT_WIDTH, available)

    def set_overlay_visible(self, visible: bool) -> None:
        if visible:
            self.show()
            self.raise_()
            if self.display_mode() == "on_change":
                self.auto_hide_timer.start(self.auto_hide_seconds() * 1000)
        else:
            self.auto_hide_timer.stop()
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


def is_revealable_media(snapshot: MediaSnapshot) -> bool:
    if snapshot.error:
        return False
    status = (snapshot.playback_status or "").casefold()
    if status in {"unknown", "error"}:
        return False
    return snapshot.has_media


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
