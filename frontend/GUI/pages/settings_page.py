import logging

from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from frontend.GUI.events import BottomBar
from frontend.services.api_client import ApiClient
from shared.config import config, reload_config, save_env

from .base_page import BasePage

logger = logging.getLogger(__name__)

# 欄位分組定義
_FIELD_GROUPS: list[dict] = [
    {
        "title": "環境設定",
        "fields": [
            {"name": "ENV", "label": "環境", "type": "combo", "options": ["dev", "prod"]},
            {
                "name": "LOG_LEVEL",
                "label": "Log Level",
                "type": "combo",
                "options": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            },
        ],
    },
    {
        "title": "應用程式路徑",
        "fields": [
            {"name": "OBS_PATH", "label": "OBS 路徑", "type": "text"},
            {"name": "OBS_CWD", "label": "OBS 工作目錄", "type": "text"},
            {"name": "ZOOM_APP_PATH", "label": "Zoom 路徑", "type": "text"},
            {"name": "WEBEX_APP_PATH", "label": "Webex 路徑", "type": "text"},
        ],
    },
    {
        "title": "OBS 場景",
        "fields": [
            {"name": "ZOOM_SCENE_NAME", "label": "Zoom 場景名稱", "type": "text"},
            {"name": "WEBEX_SCENE_NAME", "label": "Webex 場景名稱", "type": "text"},
        ],
    },
    {
        "title": "Webex 座標",
        "fields": [
            {"name": "WEBEX_GRID_POINT", "label": "Grid 座標", "type": "text"},
            {"name": "WEBEX_STACKED_POINT", "label": "Stacked 座標", "type": "text"},
            {"name": "WEBEX_SIDE_BY_SIDE_POINT", "label": "Side by Side 座標", "type": "text"},
        ],
    },
    {
        "title": "Email",
        "fields": [
            {"name": "DEFAULT_USER_EMAIL", "label": "寄件者 Email", "type": "text"},
            {"name": "EMAIL_APP_PASSWORD", "label": "Email 密碼", "type": "password"},
            {"name": "ADDRESSEES_EMAIL", "label": "收件者 Email", "type": "text"},
        ],
    },
    {
        "title": "超時 / 測試",
        "fields": [
            {
                "name": "MEETING_WAIT_TIMEOUT_IN_SECOND",
                "label": "等待超時 (秒)",
                "type": "spin",
                "min": 0,
                "max": 3600,
            },
            {
                "name": "RECORDING_DURATION_IN_MINUTE",
                "label": "錄影時長 (分)",
                "type": "spin",
                "min": 1,
                "max": 480,
            },
        ],
    },
    {
        "title": "資料庫 (需重啟)",
        "fields": [
            {"name": "MEETING_DB_URL", "label": "Meeting DB URL", "type": "readonly"},
            {"name": "SCHEDULER_DB_URL", "label": "Scheduler DB URL", "type": "readonly"},
        ],
    },
]


class SettingsPage(BasePage):
    def __init__(self, api_client: ApiClient):
        super().__init__()
        self.api_client = api_client
        self._field_widgets: dict[str, QWidget] = {}

        self._init_ui()
        self._layout_ui()
        self._signal_connect()
        self._load_current_values()

    def _init_ui(self):
        self.title = QLabel("系統設定")
        self.title.setObjectName("header")
        self.save_btn = QPushButton("儲存設定")
        self.save_btn.setMinimumHeight(45)
        self.save_btn.setStyleSheet(
            "background-color: #0078D4; color: white; font-weight: bold;"
        )

    def _layout_ui(self):
        main_layout = QVBoxLayout(self)

        # Header
        header = QHBoxLayout()
        header.addWidget(self.title)
        header.addStretch()
        main_layout.addLayout(header)

        # Scrollable content area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        content_layout = QVBoxLayout(scroll_content)

        for group_def in _FIELD_GROUPS:
            group_box = QGroupBox(group_def["title"])
            form_layout = QFormLayout(group_box)
            form_layout.setVerticalSpacing(10)
            form_layout.setFieldGrowthPolicy(
                QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
            )

            for field_def in group_def["fields"]:
                widget = self._create_field_widget(field_def)
                self._field_widgets[field_def["name"]] = widget
                form_layout.addRow(f"{field_def['label']}:", widget)

            content_layout.addWidget(group_box)

        content_layout.addStretch()
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        # Save button at bottom
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        main_layout.addLayout(btn_layout)

    def _signal_connect(self):
        self.save_btn.clicked.connect(self._on_save_clicked)

    def _create_field_widget(self, field_def: dict) -> QWidget:
        field_type = field_def["type"]

        if field_type == "combo":
            widget = QComboBox()
            widget.addItems(field_def["options"])
            widget.setMinimumHeight(30)
            return widget

        if field_type == "spin":
            widget = QSpinBox()
            widget.setMinimum(field_def.get("min", 0))
            widget.setMaximum(field_def.get("max", 99999))
            widget.setMinimumHeight(30)
            return widget

        if field_type == "password":
            widget = QLineEdit()
            widget.setEchoMode(QLineEdit.EchoMode.Password)
            widget.setMinimumHeight(30)
            return widget

        if field_type == "readonly":
            widget = QLineEdit()
            widget.setReadOnly(True)
            widget.setMinimumHeight(30)
            widget.setStyleSheet("background-color: #f0f0f0; color: #888;")
            return widget

        # default: text
        widget = QLineEdit()
        widget.setMinimumHeight(30)
        return widget

    def _load_current_values(self):
        for field_name, widget in self._field_widgets.items():
            value = getattr(config, field_name, "")
            self._set_widget_value(widget, value)

    def _set_widget_value(self, widget: QWidget, value):
        if isinstance(widget, QComboBox):
            idx = widget.findText(str(value))
            if idx >= 0:
                widget.setCurrentIndex(idx)
        elif isinstance(widget, QSpinBox):
            widget.setValue(int(value) if value else 0)
        elif isinstance(widget, QLineEdit):
            widget.setText(str(value) if value is not None else "")

    def _get_widget_value(self, widget: QWidget) -> str:
        if isinstance(widget, QComboBox):
            return widget.currentText()
        if isinstance(widget, QSpinBox):
            return str(widget.value())
        if isinstance(widget, QLineEdit):
            return widget.text()
        return ""

    def _on_save_clicked(self):
        updates: dict[str, str] = {}
        for field_name, widget in self._field_widgets.items():
            updates[field_name] = self._get_widget_value(widget)

        try:
            save_env(updates)
            changed = reload_config()

            if changed:
                BottomBar.update_status.emit(f"設定已儲存，更新 {len(changed)} 個欄位", 3)
            else:
                BottomBar.update_status.emit("設定已儲存，無欄位變更", 3)

            self._load_current_values()

        except Exception as e:
            logger.error(f"儲存設定失敗: {e}")
            BottomBar.update_status.emit(f"儲存失敗: {e}", 5)

    def showEvent(self, a0):
        try:
            super().showEvent(a0)
        except Exception:
            pass
        self._load_current_values()
