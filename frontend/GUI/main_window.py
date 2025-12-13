from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QDateTimeEdit,
    QTimeEdit,
    QSpinBox,
    QCheckBox,
    QPushButton,
    QLabel,
    QStackedWidget,
    QHBoxLayout,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QDateTime, QTime

from .pages import MeetingCreationPage, TaskQueryPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 會議管理中心")
        self.setGeometry(200, 200, 900, 700)  # 稍微加大視窗

        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        global_layout = QHBoxLayout(main_widget)

        # --- 左側：頁面導航 ---
        nav_widget = QWidget()
        nav_layout = QVBoxLayout(nav_widget)

        self.page1_btn = QPushButton("📝 創建新會議")
        self.page2_btn = QPushButton("📊 查詢排程")

        # 將按鈕設為 checkable，用於切換時的高亮狀態
        self.page1_btn.setCheckable(True)
        self.page2_btn.setCheckable(True)
        self.page1_btn.setChecked(True)  # 預設選中

        # 應用導航按鈕的 QSS 樣式
        self.page1_btn.setProperty("class", "nav_button")
        self.page2_btn.setProperty("class", "nav_button")

        nav_layout.addWidget(self.page1_btn)
        nav_layout.addWidget(self.page2_btn)
        nav_layout.addStretch()  # 推送按鈕至頂部

        # --- 右側：堆疊的頁面 ---
        self.page_stack = QStackedWidget()

        self.creation_page = MeetingCreationPage()
        self.extension_page = TaskQueryPage()

        self.page_stack.addWidget(self.creation_page)  # Index 0
        self.page_stack.addWidget(self.extension_page)  # Index 1

        self.page_stack.setCurrentIndex(1)

        # 連接按鈕到頁面切換邏輯 (與選中狀態同步)
        self.page1_btn.clicked.connect(self._nav_to_page_0)
        self.page2_btn.clicked.connect(self._nav_to_page_1)

        # 組合佈局
        global_layout.addWidget(nav_widget)
        global_layout.addWidget(self.page_stack)

        nav_widget.setFixedWidth(220)

    def _nav_to_page_0(self):
        self.page_stack.setCurrentIndex(0)
        self.page1_btn.setChecked(True)
        self.page2_btn.setChecked(False)

    def _nav_to_page_1(self):
        self.page_stack.setCurrentIndex(1)
        self.page1_btn.setChecked(False)
        self.page2_btn.setChecked(True)
