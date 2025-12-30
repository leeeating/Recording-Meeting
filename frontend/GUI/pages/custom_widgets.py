from datetime import datetime

from PyQt6.QtCore import QDate, QDateTime, QTime
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
        main_layout.setSpacing(8)  # 稍微增加元件間距

        # --- 1. 元件初始化 ---
        # 取得初始時間
        initial_datetime = QDateTime.currentDateTime().addSecs(offset_hours * 3600)

        # A. 日期選擇器
        self.date_picker = QDateTimeEdit(initial_datetime)
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDisplayFormat("yyyy/MM/dd")
        self.date_picker.setMinimumHeight(30)

        # B. 時間輸入
        self.time_edit = QTimeEdit(initial_datetime.time())
        self.time_edit.setWrapping(True)
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setMinimumHeight(30)

        # --- 2. 佈局元件 ---
        # 加上 QLabel 裝飾，並設定與截圖一致的文字
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

        # 轉換為 Python datetime
        return datetime(
            q_date.year(),
            q_date.month(),
            q_date.day(),
            q_time.hour(),
            q_time.minute(),
            q_time.second(),
        )

    def set_datetime(self, dt: datetime):
        """
        [關鍵新增] 用於從外部載入資料。
        MeetingQueryPage 在 _on_item_selected 時會呼叫此方法。
        """
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


if __name__ == "__main__":
    app = QApplication([])
    widget = DateTimeInputGroup()
    widget.show()
    app.exec()
