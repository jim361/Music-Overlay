from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QObject, Qt
from PySide6.QtGui import QAction, QActionGroup, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from app.media.media_models import MediaSnapshot
from app.overlay.overlay_window import OverlayWindow
from app.utils.paths import resource_path


class TrayIcon(QObject):
    def __init__(self, window: OverlayWindow, open_settings: Callable[[], None] | None = None) -> None:
        super().__init__(window)
        self.window = window
        self.open_settings = open_settings
        self.last_snapshot: MediaSnapshot | None = None
        self.fallback_icon = load_app_icon()

        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.fallback_icon)
        self.tray.setToolTip("Music Skin Overlay")
        self.tray.activated.connect(self._handle_activation)

        self.menu = QMenu()
        self.now_action = QAction("Now: No media playing", self)
        self.now_action.setEnabled(False)
        self.menu.addAction(self.now_action)

        self.show_overlay_action = QAction("Show overlay", self)
        self.show_overlay_action.setCheckable(True)
        self.show_overlay_action.setChecked(True)
        self.show_overlay_action.triggered.connect(self._set_overlay_visible)
        self.menu.addAction(self.show_overlay_action)

        self.menu.addSeparator()

        source_menu = self.menu.addMenu("Prefer source")
        self.source_group = QActionGroup(self)
        self.source_group.setExclusive(True)
        self.source_actions: dict[str, QAction] = {}
        for label, source in (
            ("Auto", "auto"),
            ("Spotify", "spotify"),
            ("Chrome", "chrome"),
            ("Edge", "edge"),
            ("Current Windows session", "current"),
        ):
            action = QAction(label, self)
            action.setCheckable(True)
            action.triggered.connect(lambda checked=False, value=source: self.window.set_source(value))
            self.source_group.addAction(action)
            self.source_actions[source] = action
            source_menu.addAction(action)

        refresh_action = QAction("Refresh now", self)
        refresh_action.triggered.connect(self.window.refresh)
        self.menu.addAction(refresh_action)

        if self.open_settings is not None:
            settings_action = QAction("Settings...", self)
            settings_action.triggered.connect(self.open_settings)
            self.menu.addAction(settings_action)

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self._quit)
        self.menu.addAction(quit_action)

        self.menu.aboutToShow.connect(self._sync_menu)
        self.tray.setContextMenu(self.menu)

        self.window.snapshot_updated.connect(self.update_snapshot)

    def show(self) -> None:
        self._sync_menu()
        self.tray.show()

    def update_snapshot(self, snapshot: MediaSnapshot) -> None:
        self.last_snapshot = snapshot
        title = snapshot.title or "No media playing"
        artist = snapshot.artist or ""
        tooltip = title if not artist else f"{title} - {artist}"

        self.tray.setToolTip(tooltip[:128])
        self.now_action.setText(f"Now: {title}")
        self._update_icon(snapshot)

    def _update_icon(self, snapshot: MediaSnapshot | None) -> None:
        self.tray.setIcon(self.fallback_icon)

    def _sync_menu(self) -> None:
        self.show_overlay_action.setChecked(self.window.isVisible())
        self.show_overlay_action.setText("Hide overlay" if self.window.isVisible() else "Show overlay")

        current_source = self.window.current_source()
        if current_source in self.source_actions:
            self.source_actions[current_source].setChecked(True)

        if self.last_snapshot:
            self.now_action.setText(f"Now: {self.last_snapshot.title or 'No media playing'}")

    def _set_overlay_visible(self, visible: bool) -> None:
        self.window.set_overlay_visible(visible)
        self._sync_menu()

    def _handle_activation(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.Trigger,
            QSystemTrayIcon.DoubleClick,
        ):
            self._set_overlay_visible(not self.window.isVisible())

    def _quit(self) -> None:
        self.tray.hide()
        QApplication.instance().quit()


def build_fallback_icon() -> QIcon:
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor("#1e2329"))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(4, 4, 56, 56, 12, 12)
    painter.setBrush(QColor("#FCD535"))
    painter.drawRoundedRect(18, 16, 7, 32, 3, 3)
    painter.drawRoundedRect(29, 10, 7, 38, 3, 3)
    painter.drawRoundedRect(40, 22, 7, 26, 3, 3)
    painter.end()

    return QIcon(pixmap)


def load_app_icon() -> QIcon:
    icon_path = resource_path("assets", "app_icon.ico")
    if icon_path.exists():
        icon = QIcon(str(icon_path))
        if not icon.isNull():
            return icon
    return build_fallback_icon()
