from __future__ import annotations

import argparse
import sys

from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app.config.settings_manager import SettingsManager
from app.config.theme_manager import ThemeManager
from app.media.dummy_provider import DummyProvider
from app.media.gsmtc_provider import GSMTCProvider
from app.media.session_selector import SourcePreference
from app.overlay.overlay_window import OverlayWindow
from app.settings.settings_window import SettingsWindow
from app.tray.tray_icon import TrayIcon
from app.utils.paths import resource_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Music Skin Overlay")
    parser.add_argument(
        "--provider",
        choices=("dummy", "gsmtc"),
        default="gsmtc",
        help="Data provider to use.",
    )
    parser.add_argument(
        "--source",
        choices=("auto", "spotify", "chrome", "edge", "current"),
        default=None,
        help="Preferred media source. Overrides saved settings for this run.",
    )
    parser.add_argument(
        "--theme",
        default=None,
        help="Optional theme name from the themes directory. Defaults to the built-in Binance-style skin.",
    )
    parser.add_argument(
        "--exit-after",
        type=float,
        default=None,
        help="Close automatically after N seconds. Useful for smoke tests.",
    )
    parser.add_argument(
        "--open-settings",
        action="store_true",
        help="Open the settings window on startup. Useful for smoke tests.",
    )
    return parser.parse_args()


def build_provider(args: argparse.Namespace, settings: SettingsManager):
    media_settings = settings.get("media", {})
    if args.source:
        preference = source_preference_from_name(args.source)
    else:
        preference = SourcePreference(
            selection_mode=media_settings.get("selection_mode", "auto"),
            preferred_source=media_settings.get("preferred_source", "spotify"),
        )

    if args.provider == "gsmtc":
        return GSMTCProvider(preference=preference)
    return DummyProvider()


def source_preference_from_name(source: str) -> SourcePreference:
    if source == "auto":
        return SourcePreference(selection_mode="auto", preferred_source="spotify")
    if source == "current":
        return SourcePreference(selection_mode="current", preferred_source="current")
    return SourcePreference(selection_mode="fixed", preferred_source=source)


def main() -> int:
    args = parse_args()
    settings = SettingsManager()
    theme_manager = ThemeManager()
    theme_name = args.theme or "default"
    theme = theme_manager.load(theme_name)
    provider = build_provider(args, settings)

    app = QApplication(sys.argv)
    app.setApplicationName("Music Skin Overlay")
    app.setQuitOnLastWindowClosed(False)
    icon_path = resource_path("assets", "app_icon.ico")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    window = OverlayWindow(provider=provider, theme=theme, settings=settings)
    settings_window = SettingsWindow(
        overlay=window,
        settings=settings,
    )
    window.open_settings = settings_window.open
    window.show()
    tray = TrayIcon(window, open_settings=settings_window.open)
    tray.show()

    if args.open_settings:
        QTimer.singleShot(100, settings_window.open)

    if args.exit_after is not None:
        QTimer.singleShot(max(0, int(args.exit_after * 1000)), app.quit)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
