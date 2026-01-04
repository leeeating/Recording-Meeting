from PyQt6.QtCore import Qt, QTime, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)


class ModernTimePicker(QDialog):
    """
    現代化的雙欄時間選擇器 (iOS 風格滾動列表)
    左欄：小時 (00-23)
    右欄：分鐘 (00-59)
    """

    MINUTE_INTERVAL = 1

    def __init__(self, initial_time: QTime, parent=None):
        super().__init__(parent)
        self.setWindowTitle("選擇時間")
        self.setFixedSize(320, 300)
        self.selected_time = initial_time

        self._init_ui()
        self._layout_ui()

    def _init_ui(self):
        """初始化所有元件"""
        # 標題與顯示區
        self.lbl_title = QLabel("設定時間")
        self.lbl_display = QLabel(self.selected_time.toString("HH:mm"))
        self.lbl_display.setStyleSheet("font-size: 24px; color: #61dafb;")
        self.lbl_display.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        # 小時選擇列表
        self.lbl_hour_header = QLabel("時")
        self.lbl_hour_header.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.list_hour = QListWidget()
        self.list_hour.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        for h in range(24):
            item = QListWidgetItem(f"{h:02d}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.list_hour.addItem(item)

        # 分鐘選擇列表
        self.lbl_min_header = QLabel("分")
        self.lbl_min_header.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.list_min = QListWidget()
        self.list_min.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        for m in range(0, 60, self.MINUTE_INTERVAL):
            item = QListWidgetItem(f"{m:02d}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.list_min.addItem(item)

        # init value
        self.list_hour.setCurrentRow(self.selected_time.hour())
        self.list_min.setCurrentRow(self.selected_time.minute())

        for lst in [self.list_hour, self.list_min]:
            lst.scrollToItem(
                lst.currentItem(), QAbstractItemView.ScrollHint.PositionAtCenter
            )
            lst.currentRowChanged.connect(self._update_display)

        # 4. 確定按鈕
        self.btn_ok = QPushButton("確認設定")
        self.btn_ok.clicked.connect(self.accept)

    def _layout_ui(self):
        """負責排版佈局"""
        main_layout = QVBoxLayout(self)

        # 1. 頂部 Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(self.lbl_title)
        header_layout.addStretch()
        header_layout.addWidget(self.lbl_display)
        main_layout.addLayout(header_layout)

        # 2. 中間選擇區
        selector_layout = QHBoxLayout()

        # 小時欄 (Vertical)
        vbox_h = QVBoxLayout()
        vbox_h.addWidget(self.lbl_hour_header)
        vbox_h.addWidget(self.list_hour)

        # 分鐘欄 (Vertical)
        vbox_m = QVBoxLayout()
        vbox_m.addWidget(self.lbl_min_header)
        vbox_m.addWidget(self.list_min)

        selector_layout.addLayout(vbox_h)
        selector_layout.addSpacing(10)  # 兩欄中間留點空隙
        selector_layout.addLayout(vbox_m)

        main_layout.addLayout(selector_layout)

        # 3. 底部按鈕
        main_layout.addWidget(self.btn_ok)

    def _update_display(self):
        """
        當小時或分鐘的 Row 改變時，立即更新 selected_time
        """
        h_row = self.list_hour.currentRow()
        m_row = self.list_min.currentRow()

        h = h_row if h_row != -1 else self.selected_time.hour()
        m = (
            (m_row * self.MINUTE_INTERVAL)
            if m_row != -1
            else self.selected_time.minute()
        )

        self.selected_time = QTime(h, m)
        self.lbl_display.setText(self.selected_time.toString("HH:mm"))

    def get_time(self) -> QTime:
        return self.selected_time


class TimePickerButton(QPushButton):
    """
    偽裝成輸入框的按鈕，點擊後彈出 ModernTimePicker
    (此類別維持原狀，功能單純不需要特別拆分)
    """

    timeChanged = pyqtSignal(QTime)

    def __init__(self, time: QTime = QTime(0, 0), parent=None):
        super().__init__(parent)
        self._time = time
        self.setText(time.toString("HH:mm"))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(self._show_picker)

    def _show_picker(self):
        # 使用新的 ModernTimePicker
        dlg = ModernTimePicker(self._time, self)
        if dlg.exec():
            new_time = dlg.get_time()
            self.setTime(new_time)

    def setTime(self, time: QTime):
        self._time = time
        self.setText(time.toString("HH:mm"))
        self.timeChanged.emit(time)

    def time(self) -> QTime:
        return self._time
