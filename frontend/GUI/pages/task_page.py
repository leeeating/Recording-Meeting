from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QListWidget,
    QVBoxLayout,
    QTextEdit,
    QLabel,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import sys
from typing import Dict, List, Any

# 💡 簡化的假資料：兩層結構 (會議 -> 任務清單，任務包含額外詳情)
SIMPLIFIED_TASK_DATA: Dict[str, List[str]] = {
    "會議 A (Quarterly Review)": [
        "Task 1: Prepare Q4 Slides - 到期日: 2026/01/10, 優先級: 高",
        "Task 2: Send out Agenda - 到期日: 2025/12/30, 優先級: 中",
        "Task 3: Confirm Attendees List - 到期日: 2025/12/28, 優先級: 高",
    ],
    "會議 B (Team Brainstorm)": [
        "Task 4: Research Competitors - 到期日: 2026/01/15, 優先級: 中",
        "Task 5: Draft New Product Ideas - 到期日: 2026/01/20, 優先級: 低",
    ],
    "會議 C (1-on-1 with Bob)": [
        "Task 6: Discuss Performance Metrics - 到期日: 2025/12/26, 優先級: 高"
    ],
}


class TaskQueryPage(QWidget):
    LIST_FONT_SIZE = 16

    def __init__(self, data_source: dict = SIMPLIFIED_TASK_DATA):
        super().__init__()
        self.data = data_source
        self.views = []

        self.header_label = QLabel("Task Query Page")
        self.header_label.setObjectName("header")

        self._create_widgets()
        self._set_list_font()
        self._connect_signals()
        self._setup_layout()

    def _create_widgets(self):
        """創建並配置所有 UI 元件"""

        # 任務詳情面板 (獨立區塊)
        self.detail_panel = QTextEdit()
        self.detail_panel.setReadOnly(True)
        self.detail_panel.setPlaceholderText("請點擊任務列表中的項目以查看詳情...")

        self.meeting_list = QListWidget()
        self.task_list = QListWidget()

        self.views.extend([self.meeting_list, self.task_list])
        self.meeting_list.addItems(list(self.data.keys()))

    def _setup_layout(self):

        main_layout = QVBoxLayout(self)

        self.list_container = QWidget()
        self.list_layout = QHBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(10)  # 確保兩列表之間有間距

        meeting_block = self._create_list_block("會議清單", self.meeting_list)
        self.list_layout.addWidget(meeting_block, stretch=1)
        task_block = self._create_list_block("任務列表", self.task_list)
        self.list_layout.addWidget(task_block, stretch=1)

        # 將列表容器加入主佈局
        main_layout.addWidget(self.header_label)
        main_layout.addWidget(self.list_container, stretch=1)
        main_layout.addWidget(QLabel("任務詳情:"))
        main_layout.addWidget(self.detail_panel, stretch=1)

        main_layout.addStretch()

    def _create_list_block(self, title_text: str, list_widget: QListWidget) -> QWidget:
        v_container = QWidget()
        v_layout = QVBoxLayout(v_container)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(5)

        title_label = QLabel(title_text)
        title_label.setObjectName("listTitle")
        v_layout.addWidget(title_label)
        v_layout.addWidget(list_widget)

        return v_container

    def _set_list_font(self):
        list_font = QFont()
        list_font.setPointSize(self.LIST_FONT_SIZE)

        self.meeting_list.setFont(list_font)
        self.task_list.setFont(list_font)

    def _connect_signals(self):
        """連接所有元件的信號與槽"""
        self.meeting_list.itemClicked.connect(self._handle_meeting_clicked)
        self.task_list.itemClicked.connect(self._handle_task_clicked)

    # ----------------------------------------------------------------------
    # 槽函數 (保持不變)
    # ----------------------------------------------------------------------

    def _handle_meeting_clicked(self, item):
        """處理第一層 (會議) 點擊"""
        selected_meeting = item.text()
        tasks = self.data.get(selected_meeting, [])

        self.task_list.clear()
        self.task_list.addItems(tasks)

        self.detail_panel.setText("")
        self.detail_panel.setPlaceholderText(
            f"已選中會議: {selected_meeting}\n請點擊右側欄位的任務查看詳情..."
        )

    def _handle_task_clicked(self, item):
        """處理第二層 (任務) 點擊，並在詳情面板中顯示"""
        full_task_detail = item.text()
        parts = full_task_detail.split(" - ", 1)
        task_name = parts[0]

        display_text = f"<h1>{task_name}</h1>\n\n"

        if len(parts) > 1:
            details_part = parts[1]
            details = details_part.split(", ")
            for detail in details:
                if ": " in detail:
                    key, value = detail.split(": ")
                    display_text += f"<b>{key.strip()}:</b> {value.strip()}<br>"
                else:
                    display_text += f"{detail.strip()}<br>"
        else:
            display_text += "無其他任務詳情可顯示。"

        self.detail_panel.setHtml(display_text)
