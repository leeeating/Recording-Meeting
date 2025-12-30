from typing import Tuple, Type, TypeVar

from pydantic import ValidationError
from PyQt6.QtCore import QDateTime, Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.models.schemas import MeetingCreateSchema
from frontend.events import BUS, MeetingPageSignals
from frontend.GUI.config import MEETING_LAYOUT_OPTIONS
from frontend.network import ApiClient, ApiWorker

from .custom_widgets import DateTimeInputGroup

T = TypeVar("T", bound=QWidget)
ALIGNLEFT, ALIGNRIGHT = Qt.AlignmentFlag.AlignLeft, Qt.AlignmentFlag.AlignRight
DEFAULT_WIDGET_HEIGHT = 30


class MeetingCreationPage(QWidget):
    def __init__(
        self,
        api_client: ApiClient,
    ):
        super().__init__()
        self.signals = MeetingPageSignals()
        self.api_client = api_client
        self.curr_worker = None

        self.header_label = QLabel("Meeting Information Input")
        self.header_label.setObjectName("header")

        self._create_widgets()
        self._connect_signals()
        self._setup_layout()

    def _create_widgets(self):
        # A. Meeting Info Inputs
        self.meeting_name = self._set_widget_hight(QLineEdit)
        self.meeting_name.setMinimumWidth(300)

        self.meeting_type = self._set_widget_hight(QComboBox)
        self.meeting_type.addItems(MEETING_LAYOUT_OPTIONS.keys())

        self.meeting_url = self._set_widget_hight(QLineEdit)
        self.room_id = self._set_widget_hight(QLineEdit)
        self.meeting_password = self._set_widget_hight(QLineEdit)
        self.meeting_layout = self._set_widget_hight(QComboBox)
        self.meeting_layout.setBaseSize(1500, 1)
        self.empty_label = self._set_widget_hight(QLabel)

        # B. Creator Info
        self.creator_name = self._set_widget_hight(QLineEdit)
        self.creator_email = self._set_widget_hight(QLineEdit)

        # C. Time Input Groups
        self.start_time = DateTimeInputGroup(0)
        self.end_time = DateTimeInputGroup(1)

        # D. Repeat Options
        self.repeat = QCheckBox()
        self.repeat_unit = self._set_widget_hight(QLineEdit)
        self.repeat_end_date = self._set_widget_hight(QDateTimeEdit)
        self.repeat_end_date.setCalendarPopup(True)
        self.repeat_end_date.setDisplayFormat("yyyy/MM/dd")
        self.repeat_end_date.setDateTime(QDateTime.currentDateTime())

        # E. Submit Button
        self.submit_button = QPushButton("💾 提交會議排程")
        self.submit_button.setObjectName("submitButton")
        self.submit_button.setMinimumHeight(40)

        self._update_meeting_layout(self.meeting_type.currentText())

    def _setup_layout(self):
        """設置佈局，實現左右兩欄結構"""

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.addWidget(self.header_label)

        name_widget, name_layout = self._create_form_block()
        name_layout.addRow("會議名稱:", self.meeting_name)
        main_layout.addWidget(name_widget, alignment=ALIGNLEFT)

        two_column_container = QWidget()
        two_column_layout = QHBoxLayout(two_column_container)
        # --- 左側欄 ---
        left_form_widget, left_form_layout = self._create_form_block()
        left_form_layout.addRow("會議類型:", self.meeting_type)
        left_form_layout.addRow("會議連結:", self.meeting_url)
        left_form_layout.addRow("會議識別 ID:", self.room_id)
        left_form_layout.addRow("會議密碼:", self.meeting_password)
        left_form_layout.addRow("是否重複排程:", self.repeat)
        left_form_layout.addRow("重複週期(天):", self.repeat_unit)
        left_form_layout.addRow("重複結束日期:", self.repeat_end_date)

        # --- 右側欄 ---
        right_form_widget, right_form_layout = self._create_form_block()
        right_form_layout.addRow("會議佈局:", self.meeting_layout)
        right_form_layout.addRow("建立者名稱:", self.creator_name)
        right_form_layout.addRow("建立者Email:", self.creator_email)
        right_form_layout.addRow("起始時間:", self.start_time)
        right_form_layout.addRow("結束時間:", self.end_time)

        two_column_layout.addWidget(left_form_widget, stretch=1)
        two_column_layout.addWidget(right_form_widget, stretch=1)

        # ----------------------------------------------------------------------
        main_layout.addWidget(two_column_container, alignment=ALIGNLEFT)
        main_layout.addWidget(self.submit_button, alignment=ALIGNRIGHT)
        main_layout.addStretch()

    def _connect_signals(self):
        """連接所有元件的信號與槽，包括按鈕的外部連動"""
        self.meeting_type.currentTextChanged.connect(self._update_meeting_layout)
        self.submit_button.clicked.connect(self._on_submit_meeting_request)

    def _update_meeting_layout(self, selected_type: str):
        layout_options = MEETING_LAYOUT_OPTIONS.get(selected_type, [])
        self.meeting_layout.clear()

        if layout_options:
            self.meeting_layout.addItems(layout_options)
            self.meeting_layout.setEnabled(True)
        else:
            self.meeting_layout.addItem("無可用佈局")
            self.meeting_layout.setEnabled(False)

    def _on_submit_meeting_request(self):
        """
        [槽] 接收提交按鈕的點擊事件，收集數據，發射信號給 AppController。
        """
        if self.curr_worker and self.curr_worker.isRunning():
            return

        self.submit_button.setEnabled(False)

        try:
            BUS.update_status.emit("🚀 正在提交會議排程...", 0)
            meeting_data = self._collect_data_to_schema()
            self.curr_worker = ApiWorker(self.api_client.create_meeting, meeting_data)
            self.curr_worker.finished.connect(self.curr_worker.deleteLater)
            self.curr_worker.success.connect(self._on_api_success)
            self.curr_worker.error.connect(self._on_api_error)
            self.curr_worker.start()

        except Exception as e:
            BUS.update_status.emit(str(e), 0)
            self.curr_worker = None

        finally:
            self.submit_button.setEnabled(True)

    def _on_api_success(self, result):
        """API 執行成功的回傳處理"""
        BUS.update_status.emit("✅ 會議建立成功！", 0)
        self._clear_form()

    def _on_api_error(self, error_msg):
        """API 執行失敗的回傳處理"""
        BUS.update_status.emit(f"❌ 錯誤: {error_msg}", 0)

    def _collect_data_to_schema(self) -> MeetingCreateSchema:
        schema_fields = MeetingCreateSchema.model_fields.keys()
        data = {}

        for field_name in schema_fields:
            widget = getattr(self, field_name, None)
            if widget is not None:
                value = self._get_widget_value(widget)
                data[field_name] = value

        try:
            return MeetingCreateSchema.model_validate(data)

        except ValidationError as e:
            error_messages = "".join([f"{err['loc'][0]}," for err in e.errors()])
            raise ValueError(f"輸入格式不正確：{error_messages}")

        except Exception as e:
            raise ValueError(f"數據驗證失敗: {e}")

    def _get_widget_value(self, widget):
        """根據元件類型自動決定如何取值"""
        if isinstance(widget, QLineEdit):
            return widget.text().strip() or None
        if isinstance(widget, QComboBox):
            return widget.currentText()
        if isinstance(widget, QCheckBox):
            return widget.isChecked()
        if isinstance(widget, QSpinBox):
            return widget.value()
        if isinstance(widget, QDateTimeEdit):
            return widget.dateTime().toPyDateTime()
        if isinstance(widget, DateTimeInputGroup):
            return widget.get_datetime()
        return None

    def _create_form_block(self, VSpace: int = 15) -> Tuple[QWidget, QFormLayout]:
        """創建一個標準的 QFormLayout 區塊"""
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.setVerticalSpacing(VSpace)
        form_layout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint
        )

        return form_widget, form_layout

    def _set_widget_hight(
        self, WidgetClass: Type[T], height: int = DEFAULT_WIDGET_HEIGHT
    ) -> T:
        widget = WidgetClass()
        widget.setMinimumHeight(height)
        return widget

    def _clear_form(self):
        """清空所有輸入欄位"""
        self.meeting_name.clear()
        self.meeting_type.setCurrentIndex(0)
        self.meeting_url.clear()
        self.room_id.clear()
        self.meeting_password.clear()
        self.meeting_layout.setCurrentIndex(0)
        self.creator_name.clear()
        self.creator_email.clear()
        self.start_time.reset()
        self.end_time.reset()
        self.repeat.setChecked(False)
        self.repeat_unit.clear()
        self.repeat_end_date.setDateTime(QDateTime.currentDateTime())
