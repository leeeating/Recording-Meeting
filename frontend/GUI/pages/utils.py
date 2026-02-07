from datetime import datetime
from typing import Tuple, Type, TypeVar

from PyQt6.QtCore import QDate, QDateTime, Qt, QTime, pyqtSignal
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
    QWidget,
)

from .clock_layout import TimePickerButton

T = TypeVar("T", bound=QWidget)
DEFAULT_WIDGET_HEIGHT = 30
ALIGNLEFT = Qt.AlignmentFlag.AlignLeft
ALIGNRIGHT = Qt.AlignmentFlag.AlignRight
ALIGNTOP = Qt.AlignmentFlag.AlignTop


class DateTimeInputGroup(QWidget):
    # 定義信號以利外部監聽連動邏輯
    changed = pyqtSignal()

    def __init__(self, offset_hours: int = 0, height: int = 30, parent=None):
        super().__init__(parent)
        self.offset_hours = offset_hours
        self._height = height
        self._weight = 170
        initial_dt = QDateTime.currentDateTime().addSecs(self.offset_hours * 3600)

        self._init_ui(initial_dt)
        self._setup_layout()
        self._connect_signals()

    def _init_ui(self, initial_dt):
        """僅負責建立 UI 元件與基本設定"""
        # A. 日期選擇器
        self.date_picker = QDateTimeEdit(initial_dt)
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDisplayFormat("yyyy/MM/dd")
        self.date_picker.setMinimumHeight(self._height)
        self.date_picker.setFixedWidth(self._weight)
        # self.date_picker.lineEdit().setReadOnly(True)  # type: ignore

        # B. 時間選擇器 (TimePickerButton)
        self.time_edit = TimePickerButton(initial_dt.time())
        self.time_edit.setMinimumHeight(self._height)

    def _setup_layout(self):
        """僅負責排列 UI 元件"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        layout.addWidget(QLabel("日期:"))
        layout.addWidget(self.date_picker)
        layout.addWidget(QLabel("時間:"))
        layout.addWidget(self.time_edit)
        layout.addStretch()

    def _connect_signals(self):
        """負責訊號與槽的連結"""
        self.date_picker.dateChanged.connect(self.changed.emit)

        if hasattr(self.time_edit, "timeChanged"):
            self.time_edit.timeChanged.connect(self.changed.emit)

    # --- 3. 邏輯操作方法 (Getter / Setter / Action) ---
    def get_datetime(self) -> datetime:
        """獲取目前的 datetime 物件"""
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
        """設定元件的時間與日期"""
        if not dt:
            return
        self.date_picker.setDate(QDate(dt.year, dt.month, dt.day))
        self.time_edit.setTime(QTime(dt.hour, dt.minute, dt.second))

    def reset(self):
        """根據初始的 offset_hours 重置時間"""
        target_dt = QDateTime.currentDateTime().addSecs(self.offset_hours * 3600)
        self.date_picker.setDate(target_dt.date())
        self.time_edit.setTime(target_dt.time())


class CustomLineEdit(QLineEdit):
    """
    設定寬、高、是否水平、垂直拉伸的 LineEdit
    """

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


class EmptyLabel(QLabel):
    """
    用於佔位的空白色塊，可設定固定寬高
    """

    def __init__(
        self,
        width: int | None = None,
        height: int | None = None,
        parent=None,
    ):
        super().__init__(parent)
        if width:
            self.setMinimumWidth(width)
        if height:
            self.setMinimumHeight(height)


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
