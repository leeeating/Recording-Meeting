import logging

from PyQt6.QtCore import QDateTime, Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDateTimeEdit,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.models.schemas import TaskQuerySchema, TaskResponseSchema
from frontend.services import ApiClient

from .base_page import BasePage

logger = logging.getLogger(__name__)


class TaskManagerPage(BasePage):
    def __init__(self, api_client: ApiClient, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.widget_height = 35
        self.date_width = 180
        self.header = ["會議名稱", "日期時間", "狀態"]
        self.n_header = len(self.header)

        self._create_widgets()
        self._setup_layout()
        self._connect_signals()

    def _create_widgets(self):
        """初始化所有 UI 元件"""
        # --- A. 篩選區 ---
        self.filter_group = QGroupBox("任務篩選")
        self.start_date_edit = QDateTimeEdit(QDateTime.currentDateTime().addDays(-7))
        self.end_date_edit = QDateTimeEdit(QDateTime.currentDateTime())

        for edit in [self.start_date_edit, self.end_date_edit]:
            edit.setCalendarPopup(True)
            edit.setDisplayFormat("yyyy/MM/dd")
            edit.setFixedWidth(self.date_width)
            edit.setFixedHeight(self.widget_height)

        self.filter_btn = QPushButton("查詢")
        self.clear_btn = QPushButton("重置")

        # --- B. 表格區 ---
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(self.n_header)
        self.result_table.setHorizontalHeaderLabels(self.header)

        header = self.result_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.result_table.setColumnWidth(2, 160)

        # --- C. 統計區 ---
        self.status_label = QLabel("共顯示 0 筆資料")

    def _setup_layout(self):
        """組織佈局結構"""
        main_layout = QVBoxLayout(self)

        # 篩選欄位排列
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("開始:"))
        filter_layout.addWidget(self.start_date_edit)
        filter_layout.addSpacing(10)
        filter_layout.addWidget(QLabel("結束:"))
        filter_layout.addWidget(self.end_date_edit)
        filter_layout.addStretch()
        filter_layout.addWidget(self.filter_btn)
        filter_layout.addWidget(self.clear_btn)
        self.filter_group.setLayout(filter_layout)

        # 頁面組裝
        main_layout.addWidget(self.filter_group)
        main_layout.addWidget(self.result_table, stretch=1)

        summary_layout = QHBoxLayout()
        summary_layout.addStretch()
        summary_layout.addWidget(self.status_label)
        main_layout.addLayout(summary_layout)

    def _connect_signals(self):
        """負責訊號與槽的連結"""
        self.filter_btn.clicked.connect(self.on_filter_clicked)
        self.clear_btn.clicked.connect(self.on_clear_clicked)

    # --- 邏輯操作方法 ---

    def on_clear_clicked(self):
        """重置篩選條件"""
        self.start_date_edit.setDateTime(QDateTime.currentDateTime().addDays(-7))
        self.end_date_edit.setDateTime(QDateTime.currentDateTime())
        self.result_table.setRowCount(0)
        self.update_summary(0)

    def on_filter_clicked(self):
        """執行篩選並載入資料"""
        # 1. 取得時間並封裝成 Schema
        # 設定開始為 00:00:00，結束為 23:59:59
        s_dt = (
            self.start_date_edit.dateTime()
            .toPyDateTime()
            .replace(hour=0, minute=0, second=0)
        )
        e_dt = (
            self.end_date_edit.dateTime()
            .toPyDateTime()
            .replace(hour=23, minute=59, second=59)
        )

        query_params = TaskQuerySchema(
            start_time_ge=s_dt,
            end_time_le=e_dt,
            skip=0,
            limit=200,
            sort_by="start_time",
            order="asc",
            status=None,
        )

        self.run_request(
            self.api_client.get_tasks,
            params=query_params,  # 這裡傳入篩選參數
            name="載入統計資料",
            callback=self._render_table,
        )

    STATUS_OPTIONS = ["upcoming", "recording", "completed", "error", "failed"]
    STATUS_COLORS = {"failed": "#e74c3c", "error": "#e67e22"}

    def _render_table(self, data_list: list[TaskResponseSchema]):
        """
        將 API 回傳的 List[TaskResponseSchema] 渲染至表格
        """
        self.result_table.setRowCount(0)

        if data_list is None:
            self.update_summary(0)
            return

        self.result_table.setRowCount(len(data_list))

        for row_idx, task in enumerate(data_list):
            raw_start = task.get("start_time") if isinstance(task, dict) else task.start_time
            if isinstance(raw_start, str):
                start_time_str = raw_start[:16].replace("-", "/").replace("T", " ")
            elif raw_start:
                start_time_str = raw_start.strftime("%Y/%m/%d %H:%M")
            else:
                start_time_str = "-"

            raw_status = task.get("status") if isinstance(task, dict) else task.status
            status_text = raw_status.value if hasattr(raw_status, "value") else str(raw_status)

            meeting_name = task.get("meeting_name", "") if isinstance(task, dict) else task.meeting_name
            task_id = task.get("id") if isinstance(task, dict) else task.id

            # 會議名稱 (存 task_id 到 UserRole)
            name_item = QTableWidgetItem(str(meeting_name))
            name_item.setFlags(name_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            name_item.setData(Qt.ItemDataRole.UserRole, task_id)
            self.result_table.setItem(row_idx, 0, name_item)

            # 日期時間
            time_item = QTableWidgetItem(start_time_str)
            time_item.setFlags(time_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
            time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.result_table.setItem(row_idx, 1, time_item)

            # 狀態下拉選單
            combo = QComboBox()
            combo.addItems(self.STATUS_OPTIONS)
            combo.setCurrentText(status_text)
            self._apply_combo_color(combo, status_text)
            combo.currentTextChanged.connect(
                lambda new_status, r=row_idx: self._on_status_changed(r, new_status)
            )
            self.result_table.setCellWidget(row_idx, 2, combo)

        self._update_summary_from_table()

    def _apply_combo_color(self, combo: QComboBox, status: str):
        color = self.STATUS_COLORS.get(status, "")
        if color:
            combo.setStyleSheet(f"QComboBox {{ color: {color}; }}")
        else:
            combo.setStyleSheet("")

    def _on_status_changed(self, row: int, new_status: str):
        task_id = self.result_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        combo = self.result_table.cellWidget(row, 2)
        self._apply_combo_color(combo, new_status)

        self.run_request(
            self.api_client.update_task_status,
            task_id=task_id,
            status=new_status,
            name="更新任務狀態",
            callback=lambda _: self._update_summary_from_table(),
        )

    def _update_summary_from_table(self):
        from collections import Counter

        statuses = []
        for row in range(self.result_table.rowCount()):
            combo = self.result_table.cellWidget(row, 2)
            if combo:
                statuses.append(combo.currentText())
        counter = Counter(statuses)
        self.update_summary(len(statuses), counter)

    def update_summary(self, total: int, counter=None):
        if counter is None:
            counter = {}
        upcoming = counter.get("upcoming", 0)
        recording = counter.get("recording", 0)
        completed = counter.get("completed", 0)
        error = counter.get("error", 0)
        failed = counter.get("failed", 0)
        finished = completed + error + failed
        rate = f"{(completed + error) / finished * 100:.0f}%" if finished else "-"
        self.status_label.setText(
            f"共 {total} 筆 ｜ 待執行 {upcoming} ｜ 錄製中 {recording}"
            f" ｜ 完成 {completed} ｜ 錯誤 {error} ｜ 失敗 {failed} ｜ 成功率 {rate}"
        )
