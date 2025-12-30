from collections import deque

from PyQt6.QtCore import QTimer, pyqtSlot
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from frontend.GUI.events import BUS
from frontend.network.api_client import ApiClient

from .pages import MeetingCreationPage, MeetingQueryPage, StatusPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 會議管理中心")
        # self.center()

        self.api_client = ApiClient()
        self.current_worker = None

        self.msg_queue = deque()
        self.is_displaying = False

        self._create_widgets()
        self._setup_layout()
        self._connect_signals()

        self._switch_page(1)

    def _create_widgets(self):
        """建立所有核心元件"""
        self.page1_btn = QPushButton("📝 創建會議")
        self.page2_btn = QPushButton("📊 排程任務資訊")
        self.page3_btn = QPushButton("ℹ️ 狀態頁面")

        for btn in [self.page1_btn, self.page2_btn, self.page3_btn]:
            btn.setCheckable(True)
            btn.setProperty("class", "nav_button")

        self.status_bar = self.statusBar()

        self.page_stack = QStackedWidget()
        self.creation_page = MeetingCreationPage(self.api_client)
        self.query_page = MeetingQueryPage(self.api_client)
        self.statue_page = StatusPage()

        self.page_stack.addWidget(self.creation_page)
        self.page_stack.addWidget(self.query_page)
        self.page_stack.addWidget(self.statue_page)

    def _setup_layout(self):
        """組裝佈局結構 (維持原樣)"""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.global_layout = QHBoxLayout(main_widget)

        self.nav_widget = QWidget()
        self.nav_widget.setFixedWidth(180)
        nav_layout = QVBoxLayout(self.nav_widget)
        nav_layout.addWidget(self.page1_btn)
        nav_layout.addWidget(self.page2_btn)
        nav_layout.addWidget(self.page3_btn)
        nav_layout.addStretch()

        self.global_layout.addWidget(self.nav_widget)
        self.global_layout.addWidget(self.page_stack)

    def _connect_signals(self):
        """連接所有信號"""
        self.page1_btn.clicked.connect(lambda: self._switch_page(0))
        self.page2_btn.clicked.connect(lambda: self._switch_page(1))
        self.page3_btn.clicked.connect(lambda: self._switch_page(2))
        BUS.update_status.connect(self._enqueue_status)

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
        display_time = duration * 1000 if duration > 0 else 2000  # 預設顯示 2 秒
        if self.status_bar:
            self.status_bar.showMessage(msg, display_time)
        QTimer.singleShot(display_time, self._process_queue)

    def _switch_page(self, index: int):
        self.page_stack.setCurrentIndex(index)
        self.page1_btn.setChecked(index == 0)
        self.page2_btn.setChecked(index == 1)
        self.page3_btn.setChecked(index == 2)
