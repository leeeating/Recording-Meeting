from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from frontend.services import ApiClient

from .base_page import BasePage


class StatusPage(BasePage):
    def __init__(self, api_client: ApiClient):
        super().__init__()
        self.api_client = api_client
        self.header = ["任務 ID", "會議名稱", "下次執行時間", "參數備註"]

        self._create_widgets()
        self._setup_layout()
        self._connect_signals()

        self._check_backend_status()

    def _create_widgets(self):
        """1. 建立所有 UI 元件"""
        self.header_label = QLabel("排程器監控中心")
        self.header_label.setObjectName("header")

        # 狀態燈號與文字
        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet("color: gray; font-size: 18px;")
        self.status_text = QLabel("正在初始化...")

        # 任務表格
        self.job_table = QTableWidget()
        self.job_table.setColumnCount(len(self.header))
        self.job_table.setHorizontalHeaderLabels(self.header)
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
        self.refresh_button.clicked.connect(self._check_backend_status)

    # --- 邏輯處理 ---

    def _check_backend_status(self):
        self.run_request(
            self.api_client.get_backend_status,
            name="檢查後端狀態",
            callback=self._update_ui_state,
        )
        self.load_scheduler_data()

    def _update_ui_state(self, online: bool):
        """更新 UI 視覺狀態"""
        color = "#2ecc71" if online else "#e74c3c"
        msg = "系統連線中" if online else "伺服器離線"
        self.status_dot.setStyleSheet(f"color: {color}; font-size: 18px;")
        self.status_text.setText(msg)

    def load_scheduler_data(self):
        """1. 發送非同步請求獲取排程資料"""
        self.run_request(
            self.api_client.get_scheduler_data,
            name="載入排程資料",
            callback=self._fill_table_data,
        )

    def _fill_table_data(self, jobs: list):
        """2. 真正將資料填入表格的回呼函式"""

        self.job_table.setRowCount(0)
        if not jobs:
            print("DEBUG: 資料清單為空")
            return

        self.job_table.setRowCount(len(jobs))
        for row, job in enumerate(jobs):
            # 準備各個欄位的資料
            display_data = [
                str(job.get("id", "")),
                str(job.get("name", "未命名任務")),
                str(job.get("next_run_time", "已暫停")),  # 整合暫停邏輯
                str(job.get("trigger", "")),
            ]

            for col, text in enumerate(display_data):
                item = QTableWidgetItem(text)

                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)

                # 優化 2: 文字置中對齊
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # 優化 3: 如果是「已暫停」，文字顏色變灰
                if text == "已暫停":
                    from PyQt6.QtGui import QColor

                    item.setForeground(QColor("gray"))

                self.job_table.setItem(row, col, item)
