from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QObject, Qt
from PySide6.QtGui import QAction, QActionGroup, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from app.localization import translate
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
        self.show_overlay_action = QAction(translate("show_overlay", self.language()), self)
        self.show_overlay_action.setCheckable(True)
        self.show_overlay_action.setChecked(True)
        self.show_overlay_action.triggered.connect(self._set_overlay_visible)
        self.menu.addAction(self.show_overlay_action)

        self.menu.addSeparator()

        self.source_menu = self.menu.addMenu(translate("prefer_source", self.language()))
        self.source_group = QActionGroup(self)
        self.source_group.setExclusive(True)
        self.source_actions: dict[str, QAction] = {}
        self.source_label_keys = {
            "auto": "source_auto",
            "spotify": "source_spotify",
            "chrome": "source_chrome",
            "edge": "source_edge",
            "current": "source_current",
        }
        for source, label_key in self.source_label_keys.items():
            action = QAction(translate(label_key, self.language()), self)
            action.setCheckable(True)
            action.triggered.connect(lambda checked=False, value=source: self.window.set_source(value))
            self.source_group.addAction(action)
            self.source_actions[source] = action
            self.source_menu.addAction(action)

        self.refresh_action = QAction(translate("refresh_now", self.language()), self)
        self.refresh_action.triggered.connect(self.window.refresh)
        self.menu.addAction(self.refresh_action)

        self.settings_action: QAction | None = None
        if self.open_settings is not None:
            self.settings_action = QAction(translate("settings", self.language()), self)
            self.settings_action.triggered.connect(self.open_settings)
            self.menu.addAction(self.settings_action)

        self.quit_action = QAction(translate("quit", self.language()), self)
        self.quit_action.triggered.connect(self._quit)
        self.menu.addAction(self.quit_action)

        self.menu.aboutToShow.connect(self._sync_menu)
        self.tray.setContextMenu(self.menu)

        self.window.snapshot_updated.connect(self.update_snapshot)

    def language(self) -> str:
        return self.window.language()

    def show(self) -> None:
        self._sync_menu()
        self.tray.show()

    def update_snapshot(self, snapshot: MediaSnapshot) -> None:
        self.last_snapshot = snapshot
        title = snapshot.title or translate("no_media", self.language())
        artist = snapshot.artist or ""
        tooltip = title if not artist else f"{title} - {artist}"

        self.tray.setToolTip(tooltip[:128])
        self._update_icon(snapshot)

    def _update_icon(self, snapshot: MediaSnapshot | None) -> None:
        self.tray.setIcon(self.fallback_icon)

    def _sync_menu(self) -> None:
        language = self.language()
        self.show_overlay_action.setChecked(self.window.isVisible())
        self.show_overlay_action.setText(
            translate("hide_overlay", language) if self.window.isVisible()
            else translate("show_overlay", language)
        )
        self.source_menu.setTitle(translate("prefer_source", language))
        for source, action in self.source_actions.items():
            action.setText(translate(self.source_label_keys[source], language))
        self.refresh_action.setText(translate("refresh_now", language))
        if self.settings_action is not None:
            self.settings_action.setText(translate("settings", language))
        self.quit_action.setText(translate("quit", language))

        current_source = self.window.current_source()
        if current_source in self.source_actions:
            self.source_actions[current_source].setChecked(True)

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
