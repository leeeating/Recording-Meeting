from typing import Tuple, Type, TypeVar
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QDateTimeEdit,
    QTimeEdit,
    QSpinBox,
    QCheckBox,
    QPushButton,
    QLabel,
    QHBoxLayout,
)
from PyQt6.QtCore import Qt, QDateTime, QTime

from .custom_widgets import DateTimeInputGroup

T = TypeVar("T", bound=QWidget)
ALIGNLEFT, ALIGNRIGHT = Qt.AlignmentFlag.AlignLeft, Qt.AlignmentFlag.AlignRight
DEFAULT_WIDGET_HEIGHT = 30
MEETING_LAYOUT_OPTIONS = {
    "Webex": ["網格", "堆疊", "並排"],
    "Zoom": ["演講者", "圖庫", "多位演講者", "沉浸式"],
}


class MeetingCreationPage(QWidget):
    def __init__(self):
        super().__init__()

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
        self.start_group = self._set_widget_hight(DateTimeInputGroup)
        self.end_group = self._set_widget_hight(DateTimeInputGroup)

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

    def _set_widget_hight(
        self, WidgetClass: Type[T], height: int = DEFAULT_WIDGET_HEIGHT
    ) -> T:
        widget = WidgetClass()
        widget.setMinimumHeight(height)
        return widget

    def _connect_signals(self):
        """連接所有元件的信號與槽"""
        self.meeting_type.currentTextChanged.connect(self._update_meeting_layout)

    def _create_form_block(self, VSpace: int = 15) -> Tuple[QWidget, QFormLayout]:
        """創建一個標準的 QFormLayout 區塊"""
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.setVerticalSpacing(VSpace)
        form_layout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint
        )

        return form_widget, form_layout

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
        right_form_layout.addRow("起始時間:", self.start_group)
        right_form_layout.addRow("結束時間:", self.end_group)

        two_column_layout.addWidget(left_form_widget, stretch=1)
        two_column_layout.addWidget(right_form_widget, stretch=1)

        # ----------------------------------------------------------------------
        main_layout.addWidget(two_column_container, alignment=ALIGNLEFT)
        main_layout.addWidget(self.submit_button, alignment=ALIGNRIGHT)
        main_layout.addStretch()

    def _update_meeting_layout(self, selected_type: str):
        layout_options = MEETING_LAYOUT_OPTIONS.get(selected_type, [])
        self.meeting_layout.clear()

        if layout_options:
            self.meeting_layout.addItems(layout_options)
            self.meeting_layout.setEnabled(True)
        else:
            self.meeting_layout.addItem("無可用佈局")
            self.meeting_layout.setEnabled(False)
