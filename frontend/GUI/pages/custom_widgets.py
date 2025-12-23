from PyQt6.QtCore import QDateTime, Qt
from PyQt6.QtWidgets import (
    QApplication,
    QDateTimeEdit,
    QHBoxLayout,
    QLabel,
    QTimeEdit,
    QWidget,
)


class DateTimeInputGroup(QWidget):
    def __init__(self, offset_hours: int = 0):
        super().__init__()

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # --- 1. 元件工廠 (將前面定義的工廠邏輯搬移到這裡) ---
        # A. 日期選擇器
        initial_datetime = QDateTime.currentDateTime().addSecs(offset_hours * 3600)

        self.date_picker = QDateTimeEdit(initial_datetime)
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDisplayFormat("yyyy/MM/dd")

        # B. 時間輸入
        initial_time = initial_datetime.time()
        self.time_edit = QTimeEdit(initial_time)
        self.time_edit.setWrapping(True)
        self.time_edit.setDisplayFormat("HH:mm")

        # --- 2. 佈局元件 ---
        main_layout.addWidget(QLabel("日期:"))
        main_layout.addWidget(self.date_picker)
        main_layout.addWidget(QLabel("時間:"))
        main_layout.addWidget(self.time_edit)

        main_layout.addStretch()

    def get_datetime(self) -> str:
        """
        Transform the selected date and time into an ISO 8601 formatted string.
        例如: "2023-10-05T14:30:00"
        """
        date_part = self.date_picker.date()
        time_part = self.time_edit.time()

        combined_datetime = QDateTime(date_part, time_part)

        return combined_datetime.toString(Qt.DateFormat.ISODate)

    def reset(self):
        """重置日期和時間為當前時間"""
        current_datetime = QDateTime.currentDateTime()
        self.date_picker.setDate(current_datetime.date())
        self.time_edit.setTime(current_datetime.time())


if __name__ == "__main__":
    app = QApplication([])
    widget = DateTimeInputGroup()
    widget.show()
    app.exec()
