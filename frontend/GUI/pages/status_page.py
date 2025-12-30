from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)


class StatusPage(QWidget):
    # 定義自定義信號（如果需要通知父視窗）
    status_updated = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        # 初始化核心組件
        self._create_widgets()
        self._setup_layout()
        self._connect_signals()

        # 設定自動更新定時器 (5秒更新一次)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.fetch_data_from_backend)
        self.refresh_timer.start(5000)

    def _create_widgets(self):
        """1. 建立所有 UI 元件"""
        self.header_label = QLabel("排程器監控中心")
        self.header_label.setObjectName("header")

        # 狀態燈號與文字
        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet("color: gray; font-size: 18px;")
        self.status_text = QLabel("正在初始化...")

        # 任務表格
        self.job_table = QTableWidget(0, 3)
        self.job_table.setHorizontalHeaderLabels(
            ["任務 ID", "下次執行時間", "參數備註"]
        )
        self.job_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.job_table.setAlternatingRowColors(True)  # 隔行變色，易於閱讀

        # 按鈕
        self.refresh_button = QPushButton("手動整理")

    def _setup_layout(self):
        """2. 設定佈局與元件擺放"""
        main_layout = QVBoxLayout()

        # 頂部標題與狀態列
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.status_dot)
        top_layout.addWidget(self.status_text)
        top_layout.addStretch()
        top_layout.addWidget(self.refresh_button)

        main_layout.addWidget(self.header_label)
        main_layout.addLayout(top_layout)

        # 表格區
        main_layout.addWidget(QLabel("待執行任務隊列："))
        main_layout.addWidget(self.job_table)

        self.setLayout(main_layout)

    def _connect_signals(self):
        """3. 連接按鈕與信號"""
        self.refresh_button.clicked.connect(self.fetch_data_from_backend)

    # --- 邏輯處理 ---

    def fetch_data_from_backend(self):
        """向 FastAPI 請求資料"""
        # 這裡之後會放入 requests.get("http://localhost:8000/task/scheduler/status")
        # 模擬成功後的更新動作：
        self._update_ui_state(online=True, msg="排程器正常運作中")

    def _update_ui_state(self, online: bool, msg: str):
        """更新 UI 視覺狀態"""
        color = "#2ecc71" if online else "#e74c3c"
        self.status_dot.setStyleSheet(f"color: {color}; font-size: 18px;")
        self.status_text.setText(msg)
        self.status_updated.emit(online)
