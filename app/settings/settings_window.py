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
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.config.settings_manager import SettingsManager
from app.localization import LANGUAGE_OPTIONS, translate
from app.overlay.overlay_window import OverlayWindow


SOURCE_OPTIONS = [
    ("source_auto", "auto"),
    ("source_spotify", "spotify"),
    ("source_chrome", "chrome"),
    ("source_edge", "edge"),
    ("source_current", "current"),
]

DISPLAY_MODE_OPTIONS = [
    ("mode_always", "always"),
    ("mode_on_change", "on_change"),
]

FONT_SIZE_OPTIONS = [
    ("title_size", "title_size", 9, 32, 14),
    ("detail_size", "detail_size", 8, 28, 11),
    ("meta_size", "meta_size", 8, 24, 10),
]

COLOR_OPTIONS = [
    ("title_color", "title_color", "#eaecef"),
    ("detail_color", "detail_color", "#929aa5"),
    ("meta_color", "meta_color", "#707a8a"),
    ("accent_color", "accent_color", "#FCD535"),
]

TEXT_WIDTH_OPTION = ("overlay_text_width", "text_width", 180, 760, 440)


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
        self.label_widgets: dict[str, QLabel] = {}
        self.title_label: QLabel | None = None
        self.subtitle_label: QLabel | None = None
        self.tabs: QTabWidget | None = None
        self.width_hint: QLabel | None = None
        self.reset_button: QPushButton | None = None
        self.close_button: QPushButton | None = None
        self.language_combo: QComboBox | None = None
        self.text_width_spinner: QSpinBox | None = None
        self.display_mode_combo: QComboBox | None = None
        self.auto_hide_spinner: QSpinBox | None = None
        self.title_check: QCheckBox | None = None
        self.details_check: QCheckBox | None = None

        self.setWindowTitle(self._t("settings_window_title"))
        self.setWindowFlags(Qt.Window)
        self.setMinimumWidth(520)

        self._build_ui()
        self.sync_from_settings()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        self.title_label = QLabel(self._t("settings_title"))
        self.title_label.setObjectName("settingsTitle")
        root.addWidget(self.title_label)

        self.subtitle_label = QLabel(self._t("settings_subtitle"))
        self.subtitle_label.setObjectName("settingsSubtitle")
        self.subtitle_label.setWordWrap(True)
        root.addWidget(self.subtitle_label)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        root.addWidget(divider)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs, stretch=1)

        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)
        basic_layout.setContentsMargins(2, 14, 2, 2)
        basic_layout.setSpacing(12)
        basic_form = self._create_form()
        basic_layout.addLayout(basic_form)
        basic_layout.addStretch(1)
        self.tabs.addTab(basic_tab, self._t("tab_basic"))

        self.language_combo = QComboBox()
        for label, value in LANGUAGE_OPTIONS:
            self.language_combo.addItem(label, value)
        self.language_combo.currentIndexChanged.connect(self._language_changed)
        self._add_row(basic_form, "language", self.language_combo)

        self.source_combo = QComboBox()
        for label_key, value in SOURCE_OPTIONS:
            self.source_combo.addItem(self._t(label_key), value)
        self.source_combo.currentIndexChanged.connect(self._source_changed)
        self._add_row(basic_form, "preferred_source", self.source_combo)

        self.display_mode_combo = QComboBox()
        for label_key, value in DISPLAY_MODE_OPTIONS:
            self.display_mode_combo.addItem(self._t(label_key), value)
        self.display_mode_combo.currentIndexChanged.connect(self._display_mode_changed)
        self._add_row(basic_form, "display_mode", self.display_mode_combo)

        auto_hide_row = QHBoxLayout()
        auto_hide_row.setSpacing(6)
        self.auto_hide_spinner = QSpinBox()
        self.auto_hide_spinner.setRange(1, 60)
        self.auto_hide_spinner.setSuffix(" sec")
        self.auto_hide_spinner.setButtonSymbols(QSpinBox.NoButtons)
        self.auto_hide_spinner.setAlignment(Qt.AlignCenter)
        self.auto_hide_spinner.setAccelerated(True)
        self.auto_hide_spinner.setMinimumWidth(88)
        self.auto_hide_spinner.valueChanged.connect(self._auto_hide_seconds_changed)
        auto_hide_row.addWidget(self.auto_hide_spinner)
        auto_hide_row.addStretch(1)
        self._add_row(basic_form, "show_duration", auto_hide_row)

        self.album_art_check = QCheckBox(self._t("show_thumbnail"))
        self.album_art_check.stateChanged.connect(self._album_art_changed)
        self._add_row(basic_form, "thumbnail", self.album_art_check)

        self.title_check = QCheckBox(self._t("show_title"))
        self.title_check.stateChanged.connect(self._title_changed)
        self._add_row(basic_form, "title", self.title_check)

        self.details_check = QCheckBox(self._t("show_details"))
        self.details_check.stateChanged.connect(self._details_changed)
        self._add_row(basic_form, "details", self.details_check)

        self.time_check = QCheckBox(self._t("show_time"))
        self.time_check.stateChanged.connect(self._time_changed)
        self._add_row(basic_form, "time", self.time_check)

        self.progress_check = QCheckBox(self._t("show_progress"))
        self.progress_check.stateChanged.connect(self._progress_changed)
        self._add_row(basic_form, "progress", self.progress_check)

        advanced_tab = QWidget()
        advanced_layout = QVBoxLayout(advanced_tab)
        advanced_layout.setContentsMargins(2, 14, 2, 2)
        advanced_layout.setSpacing(12)
        advanced_form = self._create_form()
        advanced_layout.addLayout(advanced_form)

        width_row = QHBoxLayout()
        width_row.setSpacing(6)
        width_min, width_max = TEXT_WIDTH_OPTION[2:4]
        decrease_width_button = QPushButton("-")
        decrease_width_button.setObjectName("stepButton")
        decrease_width_button.setFixedWidth(30)

        opacity_row = QHBoxLayout()
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setSingleStep(5)
        self.opacity_slider.valueChanged.connect(self._background_opacity_changed)
        self.opacity_value_label = QLabel("92%")
        self.opacity_value_label.setMinimumWidth(42)
        opacity_row.addWidget(self.opacity_slider, stretch=1)
        opacity_row.addWidget(self.opacity_value_label)
        self._add_row(advanced_form, "background_opacity", opacity_row)

        self.text_width_spinner = QSpinBox()
        self.text_width_spinner.setRange(width_min, width_max)
        self.text_width_spinner.setSingleStep(10)
        self.text_width_spinner.setSuffix(" px")
        self.text_width_spinner.setButtonSymbols(QSpinBox.NoButtons)
        self.text_width_spinner.setAlignment(Qt.AlignCenter)
        self.text_width_spinner.setAccelerated(True)
        self.text_width_spinner.setMinimumWidth(92)
        self.text_width_spinner.valueChanged.connect(self._text_width_changed)

        increase_width_button = QPushButton("+")
        increase_width_button.setObjectName("stepButton")
        increase_width_button.setFixedWidth(30)
        decrease_width_button.clicked.connect(self.text_width_spinner.stepDown)
        increase_width_button.clicked.connect(self.text_width_spinner.stepUp)

        width_row.addWidget(decrease_width_button)
        width_row.addWidget(self.text_width_spinner)
        width_row.addWidget(increase_width_button)
        width_row.addStretch(1)
        advanced_form.addRow(self._row_label(TEXT_WIDTH_OPTION[0]), width_row)

        self.width_hint = QLabel(self._t("text_width_hint"))
        self.width_hint.setObjectName("fieldHint")
        self.width_hint.setWordWrap(True)
        advanced_form.addRow("", self.width_hint)

        self.font_combo = QFontComboBox()
        self.font_combo.currentFontChanged.connect(self._font_family_changed)
        self._add_row(advanced_form, "font", self.font_combo)

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
            self._add_row(advanced_form, label, row)

        for label, key, default_color in COLOR_OPTIONS:
            button = QPushButton(default_color)
            button.clicked.connect(lambda checked=False, option=key: self._pick_color(option))
            self.color_buttons[key] = button
            self._add_row(advanced_form, label, button)

        advanced_layout.addStretch(1)
        self.tabs.addTab(advanced_tab, self._t("tab_advanced"))

        buttons = QHBoxLayout()
        buttons.addStretch(1)

        self.reset_button = QPushButton(self._t("reset_position"))
        self.reset_button.clicked.connect(self.overlay.reset_position)
        buttons.addWidget(self.reset_button)

        self.close_button = QPushButton(self._t("close"))
        self.close_button.clicked.connect(self.hide)
        buttons.addWidget(self.close_button)

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
            QLabel#fieldHint {
                color: #707a8a;
            }
            QFrame {
                color: #2b3139;
            }
            QTabWidget::pane {
                border: 1px solid #2b3139;
                border-radius: 6px;
                top: -1px;
            }
            QTabBar::tab {
                background: #1e2329;
                color: #929aa5;
                border: 1px solid #2b3139;
                border-bottom: 0;
                padding: 7px 14px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                color: #eaecef;
                border-color: #FCD535;
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

    def _t(self, key: str) -> str:
        return translate(key, self.overlay.language())

    def _row_label(self, key: str) -> QLabel:
        label = QLabel(self._t(key))
        self.label_widgets[key] = label
        return label

    def _add_row(self, form: QFormLayout, key: str, field) -> None:
        form.addRow(self._row_label(key), field)

    @staticmethod
    def _create_form() -> QFormLayout:
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        form.setFormAlignment(Qt.AlignTop)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(12)
        return form

    def open(self) -> None:  # type: ignore[override]
        self.sync_from_settings()
        self.show()
        self.raise_()
        self.activateWindow()

    def sync_from_settings(self) -> None:
        self._syncing = True
        if self.language_combo is not None:
            self._set_combo_value(self.language_combo, self.overlay.language())
        source = self.overlay.current_source()
        self._set_combo_value(self.source_combo, source)

        overlay_settings = self.settings.get("overlay", {})
        display_mode = str(overlay_settings.get("display_mode", "always"))
        if self.display_mode_combo is not None:
            self._set_combo_value(self.display_mode_combo, display_mode)
        if self.auto_hide_spinner is not None:
            self.auto_hide_spinner.setValue(self.overlay.auto_hide_seconds())
        self._sync_display_mode_controls()

        opacity = float(overlay_settings.get("background_opacity", 0.92))
        opacity_percent = max(0, min(100, int(round(opacity * 100))))
        self.opacity_slider.setValue(opacity_percent)
        self.opacity_value_label.setText(f"{opacity_percent}%")
        self.time_check.setChecked(bool(overlay_settings.get("show_time", True)))
        self.progress_check.setChecked(bool(overlay_settings.get("show_progress_bar", True)))
        self.album_art_check.setChecked(bool(overlay_settings.get("show_album_art", True)))
        if self.title_check is not None:
            self.title_check.setChecked(bool(overlay_settings.get("show_title", True)))
        if self.details_check is not None:
            self.details_check.setChecked(bool(overlay_settings.get("show_details", True)))
        font_family = str(overlay_settings.get("font_family", "Segoe UI"))
        self.font_combo.setCurrentFont(QFont(font_family))
        if self.text_width_spinner is not None:
            _label, key, minimum, maximum, default = TEXT_WIDTH_OPTION
            value = int(overlay_settings.get(key, default))
            self.text_width_spinner.setValue(max(minimum, min(maximum, value)))

        for _label, key, minimum, maximum, default in FONT_SIZE_OPTIONS:
            value = int(overlay_settings.get(key, default))
            self.size_spinners[key].setValue(max(minimum, min(maximum, value)))

        for _label, key, default_color in COLOR_OPTIONS:
            color = normalized_hex_color(str(overlay_settings.get(key, default_color)), default_color)
            self._set_color_button(key, color)

        self._syncing = False
        self._apply_language()

    def _language_changed(self) -> None:
        if self.language_combo is None:
            return
        language = self.language_combo.currentData()
        if self._syncing:
            self._apply_language()
            return
        if language:
            self.overlay.set_language(str(language))
        self._apply_language()

    def _source_changed(self) -> None:
        if self._syncing:
            return
        source = self.source_combo.currentData()
        if source:
            self.overlay.set_source(str(source))

    def _display_mode_changed(self) -> None:
        if self.display_mode_combo is None:
            return
        self._sync_display_mode_controls()
        if self._syncing:
            return
        mode = self.display_mode_combo.currentData()
        if mode:
            self.overlay.set_display_mode(str(mode))

    def _sync_display_mode_controls(self) -> None:
        if self.display_mode_combo is None or self.auto_hide_spinner is None:
            return
        self.auto_hide_spinner.setEnabled(self.display_mode_combo.currentData() == "on_change")

    def _auto_hide_seconds_changed(self, value: int) -> None:
        if not self._syncing:
            self.overlay.set_auto_hide_seconds(value)

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

    def _title_changed(self) -> None:
        if not self._syncing and self.title_check is not None:
            self.overlay.set_show_title(self.title_check.isChecked())

    def _details_changed(self) -> None:
        if not self._syncing and self.details_check is not None:
            self.overlay.set_show_details(self.details_check.isChecked())

    def _font_family_changed(self, font: QFont) -> None:
        if not self._syncing:
            self.overlay.set_overlay_style_option("font_family", font.family())

    def _text_width_changed(self, value: int) -> None:
        if not self._syncing:
            self.overlay.set_overlay_style_option("text_width", int(value))

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

    def _apply_language(self) -> None:
        self.setWindowTitle(self._t("settings_window_title"))
        if self.title_label is not None:
            self.title_label.setText(self._t("settings_title"))
        if self.subtitle_label is not None:
            self.subtitle_label.setText(self._t("settings_subtitle"))
        if self.tabs is not None:
            self.tabs.setTabText(0, self._t("tab_basic"))
            self.tabs.setTabText(1, self._t("tab_advanced"))
        if self.width_hint is not None:
            self.width_hint.setText(self._t("text_width_hint"))
        if self.reset_button is not None:
            self.reset_button.setText(self._t("reset_position"))
        if self.close_button is not None:
            self.close_button.setText(self._t("close"))

        for key, label in self.label_widgets.items():
            label.setText(self._t(key))

        self._refresh_combo_labels(self.source_combo, SOURCE_OPTIONS)
        if self.display_mode_combo is not None:
            self._refresh_combo_labels(self.display_mode_combo, DISPLAY_MODE_OPTIONS)

        self.album_art_check.setText(self._t("show_thumbnail"))
        if self.title_check is not None:
            self.title_check.setText(self._t("show_title"))
        if self.details_check is not None:
            self.details_check.setText(self._t("show_details"))
        self.time_check.setText(self._t("show_time"))
        self.progress_check.setText(self._t("show_progress"))

    def _refresh_combo_labels(self, combo: QComboBox, options: list[tuple[str, str]]) -> None:
        for index, (label_key, _value) in enumerate(options):
            combo.setItemText(index, self._t(label_key))


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
