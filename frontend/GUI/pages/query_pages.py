from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# 模擬資料 (保持在最外層)
MOCK_MEETINGS_DATA = {
    "M001": {
        "name": "季度業務回顧 (Q4 Review)",
        "description": "分析第四季銷售數據與 KPI 達成狀況",
        "tasks": [
            {
                "id": "T101",
                "name": "製作銷售圖表",
                "start": "09:00",
                "end": "10:00",
                "status": "待執行",
            },
            {
                "id": "T102",
                "name": "準備會議記錄",
                "start": "10:00",
                "end": "11:30",
                "status": "進行中",
            },
        ],
    },
    "M002": {
        "name": "產品腦力激盪 (Product Brainstorm)",
        "description": "討論 2026 年新功能藍圖",
        "tasks": [
            {
                "id": "T201",
                "name": "競品分析報告",
                "start": "14:00",
                "end": "15:30",
                "status": "待執行",
            }
        ],
    },
}


class TaskQueryPage(QWidget):
    STATE_ROOT = "ROOT"
    STATE_DETAIL = "DETAIL"

    def __init__(self, data_source=MOCK_MEETINGS_DATA):
        super().__init__()
        self.all_data = data_source
        self.current_state = self.STATE_ROOT
        self.active_meeting_id = None

        self._create_widgets()
        self._connect_signals()
        self._setup_layout()

        self._refresh_view()

    def _create_widgets(self):
        """1. 創建並配置所有 UI 元件"""
        # 導航元件
        self.back_btn = QPushButton("← 返回會議清單")
        self.back_btn.setFixedWidth(120)

        # 核心清單元件
        self.view_list = QListWidget()
        self.view_list.setSpacing(3)
        self.view_list.setFont(QFont("Microsoft JhengHei", 12))

    def _connect_signals(self):
        """2. 連接所有元件的信號與槽 (Observer Pattern)"""
        self.back_btn.clicked.connect(self._on_back_clicked)
        self.view_list.itemDoubleClicked.connect(self._on_item_double_clicked)

    def _setup_layout(self):
        """3. 配置佈局結構"""
        self.main_layout = QVBoxLayout(self)

        # 導航列佈局
        nav_layout = QHBoxLayout()
        nav_layout.addWidget(self.back_btn)
        nav_layout.addStretch()

        # 組裝主佈局
        self.main_layout.addLayout(nav_layout)
        self.main_layout.addWidget(self.view_list, stretch=1)

    # ----------------------------------------------------------------------
    # 邏輯控制與視圖刷新 (符合 State Pattern)
    # ----------------------------------------------------------------------

    def _refresh_view(self):
        """根據目前的狀態機切換清單內容"""
        self.view_list.clear()

        if self.current_state == self.STATE_ROOT:
            self.back_btn.setVisible(False)
            for m_id, info in self.all_data.items():
                item = QListWidgetItem(f"📁  {info['name']}")
                item.setData(Qt.ItemDataRole.UserRole, m_id)
                self.view_list.addItem(item)

        elif self.current_state == self.STATE_DETAIL:
            self.back_btn.setVisible(True)
            meeting_info = self.all_data.get(self.active_meeting_id, {})
            tasks = meeting_info.get("tasks", [])
            for task in tasks:
                display_text = f"{task['name']}  ({task['start']} - {task['end']})"
                item = QListWidgetItem(display_text)
                item.setData(Qt.ItemDataRole.UserRole, task["id"])
                self.view_list.addItem(item)

    # ----------------------------------------------------------------------
    # 事件處理 (Slots)
    # ----------------------------------------------------------------------

    def _on_item_double_clicked(self, item):
        """處理雙擊下鑽或顯示完整資訊"""
        data_id = item.data(Qt.ItemDataRole.UserRole)

        if self.current_state == self.STATE_ROOT:
            self.active_meeting_id = data_id
            self.current_state = self.STATE_DETAIL
            self._refresh_view()
        else:
            self._show_final_modal(data_id)

    def _on_back_clicked(self):
        """處理返回按鈕邏輯"""
        self.current_state = self.STATE_ROOT
        self.active_meeting_id = None
        self._refresh_view()

    def _show_final_modal(self, task_id):
        """整合最終層級的資訊展示 (Facade)"""
        meeting = self.all_data.get(self.active_meeting_id)
        if not meeting:
            return

        task = next((t for t in meeting["tasks"] if t["id"] == task_id), None)
        if not task:
            return

        title = f"完整詳細資訊 - {task['name']}"
        body = (
            f"【會議詳情】\n"
            f"名稱：{meeting['name']}\n"
            f"描述：{meeting['description']}\n\n"
            f"【任務詳情】\n"
            f"任務：{task['name']}\n"
            f"代碼：{task['id']}\n"
            f"時間：{task['start']} ~ {task['end']}\n"
            f"狀態：{task['status']}"
        )
        QMessageBox.information(self, title, body)
