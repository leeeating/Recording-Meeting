from datetime import datetime
from typing import Tuple, Type, TypeVar

from PyQt6.QtCore import QDate, QDateTime, Qt, QTime
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QTimeEdit,
    QWidget,
)

from .clock import PopUpTimeEdit

T = TypeVar("T", bound=QWidget)
DEFAULT_WIDGET_HEIGHT = 30
ALIGNLEFT = Qt.AlignmentFlag.AlignLeft
ALIGNRIGHT = Qt.AlignmentFlag.AlignRight
ALIGNTOP = Qt.AlignmentFlag.AlignTop


class DateTimeInputGroup(QWidget):
    def __init__(
        self,
        offset_hours: int = 0,
        height: int = 30,
        parent=None,
    ):
        super().__init__(parent)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        # 取得初始時間
        initial_datetime = QDateTime.currentDateTime().addSecs(offset_hours * 3600)

        # A. 日期選擇器
        self.date_picker = QDateTimeEdit(initial_datetime)
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDisplayFormat("yyyy/MM/dd")
        self.date_picker.setMinimumHeight(height)

        # B. 時間輸入
        self.time_edit = PopUpTimeEdit(initial_datetime.time())
        # self.time_edit.setWrapping(True)
        # self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setMinimumHeight(height)

        main_layout.addWidget(QLabel("日期:"))
        main_layout.addWidget(self.date_picker)
        main_layout.addWidget(QLabel("時間:"))
        main_layout.addWidget(self.time_edit)

        main_layout.addStretch()

    def get_datetime(self) -> datetime:
        """
        將選擇的日期與時間合併，並回傳 Python datetime 物件。
        這能讓 MeetingCreateSchema.model_validate 直接使用。
        """
        q_date = self.date_picker.date()
        q_time = self.time_edit.time()

        return datetime(
            q_date.year(),
            q_date.month(),
            q_date.day(),
            q_time.hour(),
            q_time.minute(),
            q_time.second(),
        )

    def set_datetime(self, dt: datetime):
        if not dt:
            return

        q_date = QDate(dt.year, dt.month, dt.day)
        q_time = QTime(dt.hour, dt.minute, dt.second)

        self.date_picker.setDate(q_date)
        self.time_edit.setTime(q_time)

    def reset(self):
        """重置日期和時間為當前時間"""
        current_datetime = QDateTime.currentDateTime()
        self.date_picker.setDate(current_datetime.date())
        self.time_edit.setTime(current_datetime.time())


class CustomLineEdit(QLineEdit):
    def __init__(
        self,
        placeholder: str = "",
        width: int = 250,
        height: int = 35,
        herizontal_stretch: bool = False,
        vertical_stretch: bool = False,
        parent=None,
    ):
        super().__init__(parent)

        self.setFixedHeight(height)
        self.setMinimumWidth(width)

        self.setPlaceholderText(placeholder)
        self.setClearButtonEnabled(True)
        self.setContentsMargins(5, 0, 5, 0)

        her = (
            QSizePolicy.Policy.Expanding
            if herizontal_stretch
            else QSizePolicy.Policy.Fixed
        )
        ver = (
            QSizePolicy.Policy.Expanding
            if vertical_stretch
            else QSizePolicy.Policy.Fixed
        )
        self.setSizePolicy(her, ver)


def fixed_width_height(
    widget: T,
    width: int = 200,
    hight: int = 30,
) -> T:
    widget.setMinimumWidth(width)
    widget.setMinimumHeight(hight)
    widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    return widget


def create_form_block(VSpace: int = 15) -> Tuple[QWidget, QFormLayout]:
    form_widget = QWidget()
    form_layout = QFormLayout(form_widget)
    form_layout.setVerticalSpacing(VSpace)
    form_layout.setFieldGrowthPolicy(
        QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
    )
    form_layout.setFormAlignment(ALIGNLEFT | ALIGNTOP)
    form_layout.setLabelAlignment(ALIGNLEFT)
    return form_widget, form_layout


def set_widget_hight(WidgetClass: Type[T], h: int = DEFAULT_WIDGET_HEIGHT) -> T:
    widget = WidgetClass()
    widget.setMinimumHeight(h)
    return widget


def get_widget_value(widget):
    if isinstance(widget, QLineEdit):
        return widget.text().strip() or None
    if isinstance(widget, QComboBox):
        return widget.currentText()
    if isinstance(widget, QCheckBox):
        return widget.isChecked()
    if isinstance(widget, QDateTimeEdit):
        return widget.dateTime().toPyDateTime()
    if isinstance(widget, DateTimeInputGroup):
        return widget.get_datetime()
    return None


if __name__ == "__main__":
    app = QApplication([])
    widget = DateTimeInputGroup()
    widget.show()
    app.exec()
