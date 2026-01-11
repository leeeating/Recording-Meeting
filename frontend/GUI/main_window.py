from collections import deque
from typing import List

from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from frontend.GUI.events import BottomBar
from frontend.services.api_client import ApiClient

from .pages import MeetingManagerPage, StatusPage, TaskManagerPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Recording Meeting")
        self.resize(1500, 800)

        self.api_client = ApiClient()

        self.msg_queue = deque()
        self.is_displaying = False

        self.PAGES_CONFIG = [
            {
                "id": "manager",
                "title": "📝 會議管理",
                "class": MeetingManagerPage,
                "args": (self.api_client,),
            },
            {
                "id": "status",
                "title": "ℹ️ 系統狀態",
                "class": StatusPage,
                "args": (self.api_client,),
            },
            {
                "id": "task",
                "title": "統計資料",
                "class": TaskManagerPage,
                "args": (),
            },
        ]

        self._create_widgets()
        self._setup_layout()
        self._connect_signals()

        self._switch_page(0)

    def _create_widgets(self):
        """建立所有核心元件：動態生成導航與頁面"""
        self.status_bar = self.statusBar()
        self.page_stack = QStackedWidget()
        self.nav_group = QButtonGroup(self)
        self.nav_buttons: List[QPushButton] = []

        # 遍歷配置清單，自動生成 UI
        for i, config in enumerate(self.PAGES_CONFIG):
            btn = QPushButton(config["title"])
            btn.setCheckable(True)
            btn.setMinimumHeight(50)
            btn.setProperty("class", "nav_button")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

            # 使用 lambda 並捕獲當前索引 i
            btn.clicked.connect(lambda _, idx=i: self._switch_page(idx))

            self.nav_group.addButton(btn, i)
            self.nav_buttons.append(btn)

            # B. 建立頁面實體並注入對應參數
            page_class = config["class"]
            page_instance = page_class(*config["args"])
            self.page_stack.addWidget(page_instance)

    def _setup_layout(self):
        """組裝佈局結構 (維持導航在左，內容在右)"""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.global_layout = QHBoxLayout(main_widget)
        self.global_layout.setContentsMargins(0, 0, 0, 0)
        self.global_layout.setSpacing(0)

        # 左側導航列
        self.nav_widget = QWidget()
        self.nav_widget.setObjectName("navWidget")
        self.nav_widget.setFixedWidth(180)

        nav_layout = QVBoxLayout(self.nav_widget)
        nav_layout.setContentsMargins(10, 20, 10, 10)
        nav_layout.setSpacing(10)

        nav_title = QLabel("功能選單")
        nav_title.setObjectName("header")
        nav_layout.addWidget(nav_title)

        for btn in self.nav_buttons:
            nav_layout.addWidget(btn)

        nav_layout.addStretch()

        # 右側內容區
        self.global_layout.addWidget(self.nav_widget)
        self.global_layout.addWidget(self.page_stack)

    def _connect_signals(self):
        """連接全域信號"""
        BottomBar.update_status.connect(self._enqueue_status)

    # ==========================================
    # 狀態列訊息隊列邏輯 (原有邏輯完整保留)
    # ==========================================

    @pyqtSlot(str)
    @pyqtSlot(str, int)
    def _enqueue_status(self, message: str, duration: int = 0):
        """收到任何地方發來的訊息，先入隊"""
        self.msg_queue.append((message, duration))
        if not self.is_displaying:
            self._process_queue()

    def _process_queue(self):
        """處理隊列中的下一條訊息"""
        if not self.msg_queue:
            self.is_displaying = False
            return

        self.is_displaying = True
        msg, duration = self.msg_queue.popleft()
        display_time = duration * 1000 if duration > 0 else 2000

        if self.status_bar:
            self.status_bar.showMessage(msg, display_time)

        # 顯示結束後自動遞迴呼叫下一條
        QTimer.singleShot(display_time, self._process_queue)

    def _switch_page(self, index: int):
        """切換頁面並同步導航按鈕狀態"""
        if index < 0 or index >= self.page_stack.count():
            return

        self.page_stack.setCurrentIndex(index)

        # 同步更新按鈕選取狀態
        btn = self.nav_group.button(index)
        if btn:
            btn.setChecked(True)
