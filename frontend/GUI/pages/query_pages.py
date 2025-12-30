from datetime import datetime
from typing import Tuple, Type, TypeVar

from pydantic import ValidationError
from PyQt6.QtCore import QDateTime, Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# 假設這些是從您的專案路徑匯入的
from app.models.schemas import MeetingCreateSchema
from frontend.GUI.config import MEETING_LAYOUT_OPTIONS
from frontend.GUI.events import BUS
from frontend.network import ApiClient, ApiWorker

from .custom_widgets import DateTimeInputGroup

T = TypeVar("T", bound=QWidget)
ALIGNLEFT = Qt.AlignmentFlag.AlignLeft
DEFAULT_WIDGET_HEIGHT = 30

MOCK_MEETINGS_DATA = {
    "M001": {
        "meeting_name": "季度業務回顧 (Q4 Review)",
        "meeting_type": "Webex",
        "meeting_url": "webex.com/meet/q4",
        "room_id": "123456",
        "meeting_password": "password123",
        "meeting_layout": "網格",
        "creator_name": "王小明",
        "creator_email": "ming@example.com",
        "start_time": "2025-12-30T20:01:00Z",
        "end_time": "2025-12-30T21:01:00Z",
        "repeat": "true",
        "repeat_unit": 7,
        "repeat_end_date": "2026-01-30T00:00:00Z",
    }
}


class MeetingQueryPage(QWidget):
    def __init__(
        self,
        api_client: ApiClient,
        data_source=MOCK_MEETINGS_DATA,
    ):
        super().__init__()
        self.api_client = api_client
        self.all_data = data_source
        self.active_meeting_id = None
        self.curr_worker = None

        self._create_widgets()
        self._setup_layout()
        self._connect_signals()
        self._refresh_list()

    def _create_widgets(self):
        """1. 創建 UI 元件，使用與建立頁面相同的輔助方法"""
        # --- 上方清單 ---
        self.list_label = QLabel("📅 既有會議清單")
        self.list_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        self.filter_upcoming_chk = QCheckBox("僅顯示尚未開始的會議")
        # self.filter_upcoming_chk.setStyleSheet("color: #0078D4; font-weight: bold;")

        self.view_list = QListWidget()
        self.view_list.setMinimumHeight(100)

        # --- 下方編輯區容器 ---
        self.edit_group = QGroupBox()
        self.edit_group.setObjectName("editGroup")

        # A. 會議基本資訊 (對應 Schema 欄位名稱)
        self.meeting_name = self._set_widget_hight(QLineEdit)
        self.meeting_name.setMinimumWidth(300)

        self.meeting_type = self._set_widget_hight(QComboBox)
        self.meeting_type.addItems(MEETING_LAYOUT_OPTIONS.keys())

        self.meeting_url = self._set_widget_hight(QLineEdit)
        self.room_id = self._set_widget_hight(QLineEdit)
        self.meeting_password = self._set_widget_hight(QLineEdit)
        self.meeting_layout = self._set_widget_hight(QComboBox)

        # B. 建立者資訊
        self.creator_name = self._set_widget_hight(QLineEdit)
        self.creator_email = self._set_widget_hight(QLineEdit)

        # C. 時間元件 (使用自定義 DateTimeInputGroup)
        self.start_time = DateTimeInputGroup(0)
        self.end_time = DateTimeInputGroup(1)

        # D. 重複選項
        self.repeat = QCheckBox()
        self.repeat_unit = self._set_widget_hight(QLineEdit)
        self.repeat_end_date = self._set_widget_hight(QDateTimeEdit)
        self.repeat_end_date.setCalendarPopup(True)
        self.repeat_end_date.setDisplayFormat("yyyy/MM/dd")

        # E. 功能按鈕
        self.save_button = QPushButton("💾 儲存變更內容")
        self.save_button.setObjectName("submitButton")
        self.save_button.setMinimumHeight(40)

    def _setup_layout(self):
        """2. 設置佈局，實現上下分區與雙欄結構"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 上方：清單區
        header_layout = QHBoxLayout()
        header_layout.addWidget(self.list_label)
        header_layout.addStretch()
        header_layout.addWidget(self.filter_upcoming_chk)
        main_layout.addLayout(header_layout)

        main_layout.addWidget(self.view_list, stretch=1)

        # 下方：編輯區內容佈局
        edit_inner_layout = QVBoxLayout(self.edit_group)

        # 會議名稱列 (滿版)
        name_widget, name_layout = self._create_form_block()
        name_layout.addRow("會議名稱:", self.meeting_name)
        edit_inner_layout.addWidget(name_widget, alignment=ALIGNLEFT)

        # 雙欄位容器
        two_column_container = QWidget()
        two_column_layout = QHBoxLayout(two_column_container)
        two_column_layout.setContentsMargins(0, 0, 0, 0)

        # --- 左側欄 ---
        left_widget, left_layout = self._create_form_block()
        left_layout.addRow("會議類型:", self.meeting_type)
        left_layout.addRow("會議連結:", self.meeting_url)
        left_layout.addRow("會議識別 ID:", self.room_id)
        left_layout.addRow("會議密碼:", self.meeting_password)
        left_layout.addRow("是否重複排程:", self.repeat)
        left_layout.addRow("重複週期(天):", self.repeat_unit)
        left_layout.addRow("結束日期:", self.repeat_end_date)

        # --- 右側欄 ---
        right_widget, right_layout = self._create_form_block()
        right_layout.addRow("會議佈局:", self.meeting_layout)
        right_layout.addRow("建立者名稱:", self.creator_name)
        right_layout.addRow("建立者 Email:", self.creator_email)
        right_layout.addRow("起始時間:", self.start_time)
        right_layout.addRow("結束時間:", self.end_time)

        two_column_layout.addWidget(left_widget, stretch=1)
        two_column_layout.addWidget(right_widget, stretch=1)
        edit_inner_layout.addWidget(two_column_container)

        # 按鈕列
        edit_inner_layout.addWidget(
            self.save_button, alignment=Qt.AlignmentFlag.AlignRight
        )

        main_layout.addWidget(self.edit_group, stretch=0)

    def _connect_signals(self):
        """3. 信號連接"""
        self.view_list.itemClicked.connect(self._on_item_selected)
        self.meeting_type.currentTextChanged.connect(self._update_meeting_layout)
        self.save_button.clicked.connect(self._on_save_meeting_request)
        self.filter_upcoming_chk.stateChanged.connect(self._refresh_list)

    # --- 邏輯處理方法 ---

    def _refresh_list(self):
        """更新清單內容，包含時間篩選邏輯"""
        self.view_list.clear()
        now = datetime.now()
        only_upcoming = self.filter_upcoming_chk.isChecked()

        for m_id, info in self.all_data.items():
            # 解析會議開始時間
            try:
                start_time_str = info.get("start_time", "")
                # 將 ISO 格式字串轉換為 Python datetime 物件進行比較
                meeting_start_dt = datetime.fromisoformat(
                    start_time_str.replace("Z", "+00:00")
                )
                # 如果是 UTC 時間，需與本地時間統一 (此處假設 info 為 ISO 格式)
                meeting_start_dt = meeting_start_dt.replace(tzinfo=None)
            except Exception:
                meeting_start_dt = now  # 解析失敗時預設顯示

            # 篩選邏輯：如果勾選「僅顯示未來」，且會議時間早於現在，則跳過
            if only_upcoming and meeting_start_dt < now:
                continue

            # 建立清單項目
            item = QListWidgetItem(f"📅 {info.get('meeting_name', '未命名會議')}")
            # 可以在文字後方標註狀態
            if meeting_start_dt < now:
                item.setText(item.text() + " (已過期)")
                item.setForeground(Qt.GlobalColor.gray)

            item.setData(Qt.ItemDataRole.UserRole, m_id)
            self.view_list.addItem(item)

        # 重新整理時若沒有選中項目，禁用編輯區
        self.edit_group.setEnabled(False)

    def _on_item_selected(self, item):
        """當選取清單項目時，載入資料並轉換格式"""
        m_id = item.data(Qt.ItemDataRole.UserRole)
        data = self.all_data.get(m_id)
        if not data:
            return

        self.active_meeting_id = m_id
        self.edit_group.setEnabled(True)

        # 載入純文字與選項
        self.meeting_name.setText(data.get("meeting_name", ""))
        self.meeting_type.setCurrentText(data.get("meeting_type", ""))
        self._update_meeting_layout(data.get("meeting_type", ""))
        self.meeting_layout.setCurrentText(data.get("meeting_layout", ""))

        self.meeting_url.setText(data.get("meeting_url", ""))
        self.room_id.setText(data.get("room_id", ""))
        self.meeting_password.setText(data.get("meeting_password", ""))
        self.creator_name.setText(data.get("creator_name", ""))
        self.creator_email.setText(data.get("creator_email", ""))

        self.repeat.setChecked(str(data.get("repeat", "")).lower() == "true")
        self.repeat_unit.setText(str(data.get("repeat_unit", "0")))

        # 處理日期時間 (ISO String -> QDateTime)
        s_dt = QDateTime.fromString(data["start_time"], Qt.DateFormat.ISODate)
        self.start_time.set_datetime(s_dt.toPyDateTime())

        e_dt = QDateTime.fromString(data["end_time"], Qt.DateFormat.ISODate)
        self.end_time.set_datetime(e_dt.toPyDateTime())

        r_dt = QDateTime.fromString(data["repeat_end_date"], Qt.DateFormat.ISODate)
        self.repeat_end_date.setDateTime(r_dt)

    def _on_save_meeting_request(self):
        """處理儲存邏輯，包含驗證與 API Worker"""
        if self.curr_worker and self.curr_worker.isRunning():
            return

        try:
            # 1. 收集並驗證數據
            updated_data = self._collect_data_to_schema()

            # 2. 啟動異步 Worker (假設 api_client 有 update_meeting 方法)
            BUS.update_status.emit(f"🔄 正在更新會議: {self.active_meeting_id}...", 0)
            self.save_button.setEnabled(False)

            self.curr_worker = ApiWorker(
                self.api_client.update_meeting, self.active_meeting_id, updated_data
            )
            self.curr_worker.success.connect(self._on_api_success)
            self.curr_worker.error.connect(self._on_api_error)
            self.curr_worker.start()

        except ValueError as e:
            BUS.update_status.emit(str(e), 0)
            QMessageBox.warning(self, "驗證失敗", str(e))

    def _on_api_success(self, result):
        BUS.update_status.emit("✅ 會議資料更新成功！", 0)
        self.save_button.setEnabled(True)
        # 更新本地 Mock Data 以利即時反映在介面
        # ... 更新 self.all_data 邏輯 ...
        self._refresh_list()

    def _on_api_error(self, error_msg):
        BUS.update_status.emit(f"❌ 更新失敗: {error_msg}", 0)
        self.save_button.setEnabled(True)

    # --- 繼承自建立頁面的輔助工具函數 ---

    def _collect_data_to_schema(self) -> MeetingCreateSchema:
        schema_fields = MeetingCreateSchema.model_fields.keys()
        data = {}
        for field_name in schema_fields:
            widget = getattr(self, field_name, None)
            if widget is not None:
                data[field_name] = self._get_widget_value(widget)
        try:
            return MeetingCreateSchema.model_validate(data)
        except ValidationError as e:
            error_messages = "".join([f"{err['loc'][0]}," for err in e.errors()])
            raise ValueError(f"欄位格式錯誤：{error_messages}")

    def _get_widget_value(self, widget):
        if isinstance(widget, QLineEdit):
            return widget.text().strip() or None
        if isinstance(widget, QComboBox):
            return widget.currentText()
        if isinstance(widget, QCheckBox):
            return widget.isChecked()
        if isinstance(widget, QDateTimeEdit):
            return widget.dateTime().toPyDateTime()
        if isinstance(widget, DateTimeInputGroup):
            return widget.get_datetime()
        return None

    def _create_form_block(self, VSpace: int = 15) -> Tuple[QWidget, QFormLayout]:
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.setVerticalSpacing(VSpace)
        form_layout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint
        )
        return form_widget, form_layout

    def _set_widget_hight(
        self, WidgetClass: Type[T], height: int = DEFAULT_WIDGET_HEIGHT
    ) -> T:
        widget = WidgetClass()
        widget.setMinimumHeight(height)
        return widget

    def _update_meeting_layout(self, selected_type: str):
        layout_options = MEETING_LAYOUT_OPTIONS.get(selected_type, [])
        self.meeting_layout.clear()
        if layout_options:
            self.meeting_layout.addItems(layout_options)
            self.meeting_layout.setEnabled(True)
        else:
            self.meeting_layout.addItem("無可用佈局")
            self.meeting_layout.setEnabled(False)
