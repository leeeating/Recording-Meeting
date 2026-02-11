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
from .utils import CustomLineEdit, fixed_width_height

logger = logging.getLogger(__name__)

# 欄位分組定義
_FIELD_GROUPS: list[dict] = [
    {
        "title": "環境設定",
        "fields": [
            {
                "name": "ENV",
                "label": "環境",
                "type": "combo",
                "options": ["dev", "prod"],
            },
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
            {
                "name": "WEBEX_SIDE_BY_SIDE_POINT",
                "label": "Side by Side 座標",
                "type": "text",
            },
        ],
    },
    {
        "title": "Email",
        "fields": [
            {"name": "DEFAULT_USER_EMAIL", "label": "寄件者 Email", "type": "text"},
            {"name": "EMAIL_APP_PASSWORD", "label": "Email 密碼", "type": "password"},
            {"name": "ADDRESSEES_EMAIL", "label": "收件者 Email", "type": "email_list"},
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
            {
                "name": "SCHEDULER_DB_URL",
                "label": "Scheduler DB URL",
                "type": "readonly",
            },
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
            group_box.setStyleSheet("QGroupBox::title { font-size: 18px; }")
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
            widget = fixed_width_height(QComboBox())
            widget.addItems(field_def["options"])
            widget.setMinimumHeight(50)
            return widget

        if field_type == "spin":
            widget = QSpinBox()
            widget.setMinimum(field_def.get("min", 0))
            widget.setMaximum(field_def.get("max", 99999))
            widget.setMinimumHeight(30)
            return widget

        if field_type == "password":
            widget = CustomLineEdit()
            widget.setEchoMode(QLineEdit.EchoMode.Password)
            return widget

        if field_type == "email_list":
            return EmailListWidget()

        if field_type == "readonly":
            widget = CustomLineEdit()
            widget.setReadOnly(True)
            widget.setStyleSheet("background-color: #f0f0f0; color: #888;")
            return widget

        # default: text
        return CustomLineEdit()

    def _load_current_values(self):
        for field_name, widget in self._field_widgets.items():
            value = getattr(config, field_name, "")
            self._set_widget_value(widget, value)

    def _set_widget_value(self, widget: QWidget, value):
        if isinstance(widget, EmailListWidget):
            widget.set_value(str(value) if value else "")
        elif isinstance(widget, QComboBox):
            idx = widget.findText(str(value))
            if idx >= 0:
                widget.setCurrentIndex(idx)
        elif isinstance(widget, QSpinBox):
            widget.setValue(int(value) if value else 0)
        elif isinstance(widget, QLineEdit):
            widget.setText(str(value) if value is not None else "")

    def _get_widget_value(self, widget: QWidget) -> str:
        if isinstance(widget, EmailListWidget):
            return widget.get_value()
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
                BottomBar.update_status.emit(
                    f"設定已儲存，更新 {len(changed)} 個欄位", 3
                )
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


class EmailListWidget(QWidget):
    """可動態新增/刪除多筆 email 的輸入元件。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows_layout = QVBoxLayout()
        self._rows_layout.setContentsMargins(0, 0, 0, 0)
        self._rows_layout.setSpacing(6)

        self._add_btn = QPushButton("＋ 新增收件者")
        self._add_btn.setFixedHeight(50)
        self._add_btn.clicked.connect(lambda: self._add_row(""))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self._rows_layout)
        layout.addWidget(self._add_btn)

    # --- public API ---

    def set_value(self, comma_str: str):
        """逗號分隔字串拆成多行顯示。"""
        self._clear_rows()
        emails = [e.strip() for e in comma_str.split(",") if e.strip()]
        if not emails:
            emails = [""]
        for email in emails:
            self._add_row(email)

    def get_value(self) -> str:
        """收集非空 email，逗號串接回傳。"""
        values = []
        for i in range(self._rows_layout.count()):
            item = self._rows_layout.itemAt(i)
            if item is None:
                continue
            row_widget = item.widget()
            if row_widget is None:
                continue
            line_edit = row_widget.findChild(CustomLineEdit)
            if line_edit:
                text = line_edit.text().strip()
                if text:
                    values.append(text)
        return ",".join(values)

    # --- internal ---

    def _add_row(self, text: str):
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(4)

        line_edit = CustomLineEdit(
            placeholder="example@email.com", herizontal_stretch=True
        )
        line_edit.setText(text)
        h.addWidget(line_edit, 1)

        del_btn = QPushButton("")
        del_btn.setFixedSize(36, 36)
        del_btn.setStyleSheet(
            "QPushButton { color: #ff6666; font-weight: bold; font-size: 14px; }"
        )
        del_btn.clicked.connect(lambda: self._remove_row(row))
        h.addWidget(del_btn, 0)

        self._rows_layout.addWidget(row)
        self._update_delete_buttons()

    def _remove_row(self, row: QWidget):
        self._rows_layout.removeWidget(row)
        row.deleteLater()
        self._update_delete_buttons()

    def _update_delete_buttons(self):
        """只剩一行時隱藏刪除按鈕。"""
        count = self._rows_layout.count()
        for i in range(count):
            item = self._rows_layout.itemAt(i)
            if item is None:
                continue
            row_widget = item.widget()
            if row_widget is None:
                continue
            del_btn = row_widget.findChild(QPushButton)
            if del_btn:
                del_btn.setVisible(count > 1)

    def _clear_rows(self):
        while self._rows_layout.count():
            item = self._rows_layout.takeAt(0)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
