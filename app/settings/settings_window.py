from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QFormLayout,
    QFontComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.config.settings_manager import SettingsManager
from app.overlay.overlay_window import OverlayWindow


SOURCE_OPTIONS = [
    ("Auto", "auto"),
    ("Spotify", "spotify"),
    ("Chrome", "chrome"),
    ("Edge", "edge"),
    ("Current Windows session", "current"),
]

FONT_SIZE_OPTIONS = [
    ("Title size", "title_size", 9, 32, 14),
    ("Detail size", "detail_size", 8, 28, 11),
    ("Meta size", "meta_size", 8, 24, 10),
]

COLOR_OPTIONS = [
    ("Title color", "title_color", "#eaecef"),
    ("Detail color", "detail_color", "#929aa5"),
    ("Meta color", "meta_color", "#707a8a"),
    ("Accent color", "accent_color", "#FCD535"),
]


class SettingsWindow(QWidget):
    def __init__(
        self,
        *,
        overlay: OverlayWindow,
        settings: SettingsManager,
    ) -> None:
        super().__init__()
        self.overlay = overlay
        self.settings = settings
        self._syncing = False
        self.size_spinners: dict[str, QSpinBox] = {}
        self.color_buttons: dict[str, QPushButton] = {}

        self.setWindowTitle("Music Skin Overlay Settings")
        self.setWindowFlags(Qt.Window)
        self.setMinimumWidth(440)

        self._build_ui()
        self.sync_from_settings()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        title = QLabel("Music Skin Overlay")
        title.setObjectName("settingsTitle")
        root.addWidget(title)

        subtitle = QLabel("Tune the source and compact now-playing display.")
        subtitle.setObjectName("settingsSubtitle")
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        root.addWidget(divider)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        form.setFormAlignment(Qt.AlignTop)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(12)
        root.addLayout(form)

        self.source_combo = QComboBox()
        for label, value in SOURCE_OPTIONS:
            self.source_combo.addItem(label, value)
        self.source_combo.currentIndexChanged.connect(self._source_changed)
        form.addRow("Preferred source", self.source_combo)

        opacity_row = QHBoxLayout()
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setSingleStep(5)
        self.opacity_slider.valueChanged.connect(self._background_opacity_changed)
        self.opacity_value_label = QLabel("92%")
        self.opacity_value_label.setMinimumWidth(42)
        opacity_row.addWidget(self.opacity_slider, stretch=1)
        opacity_row.addWidget(self.opacity_value_label)
        form.addRow("Background opacity", opacity_row)

        self.time_check = QCheckBox("Show time")
        self.time_check.stateChanged.connect(self._time_changed)
        form.addRow("Time", self.time_check)

        self.progress_check = QCheckBox("Show progress bar")
        self.progress_check.stateChanged.connect(self._progress_changed)
        form.addRow("Progress", self.progress_check)

        self.album_art_check = QCheckBox("Show thumbnail")
        self.album_art_check.stateChanged.connect(self._album_art_changed)
        form.addRow("Thumbnail", self.album_art_check)

        self.font_combo = QFontComboBox()
        self.font_combo.currentFontChanged.connect(self._font_family_changed)
        form.addRow("Font", self.font_combo)

        for label, key, minimum, maximum, _default in FONT_SIZE_OPTIONS:
            row = QHBoxLayout()
            row.setSpacing(6)

            decrease_button = QPushButton("-")
            decrease_button.setObjectName("stepButton")
            decrease_button.setFixedWidth(30)

            spinner = QSpinBox()
            spinner.setRange(minimum, maximum)
            spinner.setButtonSymbols(QSpinBox.NoButtons)
            spinner.setAlignment(Qt.AlignCenter)
            spinner.setAccelerated(True)
            spinner.setMinimumWidth(64)
            spinner.valueChanged.connect(
                lambda value, option=key: self._font_size_changed(option, value)
            )

            increase_button = QPushButton("+")
            increase_button.setObjectName("stepButton")
            increase_button.setFixedWidth(30)
            decrease_button.clicked.connect(spinner.stepDown)
            increase_button.clicked.connect(spinner.stepUp)

            row.addWidget(decrease_button)
            row.addWidget(spinner)
            row.addWidget(increase_button)
            row.addStretch(1)

            self.size_spinners[key] = spinner
            form.addRow(label, row)

        for label, key, default_color in COLOR_OPTIONS:
            button = QPushButton(default_color)
            button.clicked.connect(lambda checked=False, option=key: self._pick_color(option))
            self.color_buttons[key] = button
            form.addRow(label, button)

        root.addStretch(1)

        buttons = QHBoxLayout()
        buttons.addStretch(1)

        reset_button = QPushButton("Reset Position")
        reset_button.clicked.connect(self.overlay.reset_position)
        buttons.addWidget(reset_button)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.hide)
        buttons.addWidget(close_button)

        root.addLayout(buttons)

        self.setStyleSheet(
            """
            QWidget {
                background: #0b0e11;
                color: #eaecef;
                font-family: "Segoe UI";
                font-size: 12px;
            }
            QLabel#settingsTitle {
                font-size: 18px;
                font-weight: 650;
                color: #f5f5f5;
            }
            QLabel#settingsSubtitle {
                color: #707a8a;
            }
            QFrame {
                color: #2b3139;
            }
            QComboBox, QPushButton, QSpinBox {
                background: #1e2329;
                color: #eaecef;
                border: 1px solid #2b3139;
                border-radius: 6px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                border-color: #FCD535;
            }
            QPushButton {
                min-height: 28px;
                padding: 4px 12px;
            }
            QPushButton#stepButton {
                min-width: 30px;
                max-width: 30px;
                padding: 4px 0;
                font-size: 14px;
                font-weight: 700;
            }
            QCheckBox {
                color: #eaecef;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #2b3139;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #FCD535;
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QSlider::sub-page:horizontal {
                background: #FCD535;
                border-radius: 3px;
            }
            """
        )

    def open(self) -> None:  # type: ignore[override]
        self.sync_from_settings()
        self.show()
        self.raise_()
        self.activateWindow()

    def sync_from_settings(self) -> None:
        self._syncing = True
        source = self.overlay.current_source()
        self._set_combo_value(self.source_combo, source)

        overlay_settings = self.settings.get("overlay", {})
        opacity = float(overlay_settings.get("background_opacity", 0.92))
        opacity_percent = max(0, min(100, int(round(opacity * 100))))
        self.opacity_slider.setValue(opacity_percent)
        self.opacity_value_label.setText(f"{opacity_percent}%")
        self.time_check.setChecked(bool(overlay_settings.get("show_time", True)))
        self.progress_check.setChecked(bool(overlay_settings.get("show_progress_bar", True)))
        self.album_art_check.setChecked(bool(overlay_settings.get("show_album_art", True)))
        font_family = str(overlay_settings.get("font_family", "Segoe UI"))
        self.font_combo.setCurrentFont(QFont(font_family))

        for _label, key, minimum, maximum, default in FONT_SIZE_OPTIONS:
            value = int(overlay_settings.get(key, default))
            self.size_spinners[key].setValue(max(minimum, min(maximum, value)))

        for _label, key, default_color in COLOR_OPTIONS:
            color = normalized_hex_color(str(overlay_settings.get(key, default_color)), default_color)
            self._set_color_button(key, color)

        self._syncing = False

    def _source_changed(self) -> None:
        if self._syncing:
            return
        source = self.source_combo.currentData()
        if source:
            self.overlay.set_source(str(source))

    def _background_opacity_changed(self) -> None:
        opacity = self.opacity_slider.value()
        self.opacity_value_label.setText(f"{opacity}%")
        if not self._syncing:
            self.overlay.set_background_opacity(opacity / 100)

    def _time_changed(self) -> None:
        if not self._syncing:
            self.overlay.set_show_time(self.time_check.isChecked())

    def _progress_changed(self) -> None:
        if not self._syncing:
            self.overlay.set_show_progress_bar(self.progress_check.isChecked())

    def _album_art_changed(self) -> None:
        if not self._syncing:
            self.overlay.set_show_album_art(self.album_art_check.isChecked())

    def _font_family_changed(self, font: QFont) -> None:
        if not self._syncing:
            self.overlay.set_overlay_style_option("font_family", font.family())

    def _font_size_changed(self, key: str, value: int) -> None:
        if not self._syncing:
            self.overlay.set_overlay_style_option(key, int(value))

    def _pick_color(self, key: str) -> None:
        if self._syncing:
            return

        current = self.color_buttons[key].text()
        initial = QColor(current if current.startswith("#") else "#FFFFFF")
        color = QColorDialog.getColor(initial, self, "Choose color")
        if not color.isValid():
            return

        value = color.name().upper()
        self._set_color_button(key, value)
        self.overlay.set_overlay_style_option(key, value)

    def _set_color_button(self, key: str, color: str) -> None:
        button = self.color_buttons[key]
        button.setText(color)
        button.setStyleSheet(
            f"""
            QPushButton {{
                background: {color};
                color: {contrast_text_color(color)};
                border: 1px solid #2b3139;
                border-radius: 6px;
                padding: 4px 8px;
                min-height: 28px;
            }}
            """
        )

    @staticmethod
    def _set_combo_value(combo: QComboBox, value: str) -> None:
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)


def normalized_hex_color(value: str, fallback: str) -> str:
    color = value.strip()
    if len(color) == 7 and color.startswith("#"):
        try:
            int(color[1:], 16)
        except ValueError:
            return fallback
        return color.upper()
    return fallback


def contrast_text_color(color: str) -> str:
    color = normalized_hex_color(color, "#1e2329").lstrip("#")
    red = int(color[0:2], 16)
    green = int(color[2:4], 16)
    blue = int(color[4:6], 16)
    brightness = (red * 299 + green * 587 + blue * 114) / 1000
    return "#0b0e11" if brightness > 145 else "#eaecef"
