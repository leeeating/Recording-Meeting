from datetime import datetime

from pydantic import ValidationError
from PyQt6.QtCore import QDateTime, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.models.schemas import MeetingCreateSchema
from frontend.GUI.events import BottomBar
from frontend.services.meeting_service import MeetingService

from .utils import (
    CustomLineEdit,
    DateTimeInputGroup,
    create_form_block,
    fixed_width_height,
    get_widget_value,
)

ALIGNLEFT = Qt.AlignmentFlag.AlignLeft
ALIGNRIGHT = Qt.AlignmentFlag.AlignRight
ALIGNTOP = Qt.AlignmentFlag.AlignTop

MEETING_LAYOUT_OPTIONS = {
    "Webex": ["網格", "堆疊", "並排"],
    "Zoom": ["演講者", "圖庫", "多位演講者", "沉浸式"],
}

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
    },
    "M002": {
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
    },
    "M003": {
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
    },
    "M004": {
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
    },
}


class MeetingManagerPage(QWidget):
    def __init__(self, service: MeetingService, data_source: dict = MOCK_MEETINGS_DATA):
        super().__init__()
        self.service = service
        self.all_data = data_source
        self.active_meeting_id = None
        self._worker_ref = None

        self._init_ui()
        self._layout_ui()
        self._connect_method()

        self._refresh_list()

    def _init_ui(self):
        self.title = QLabel("會議清單")
        self.title.setObjectName("header")
        self.add_new_btn = QPushButton("＋建立新會議")
        self.filter_chk = QCheckBox("僅顯示尚未開始的會議")

        self.view_list = QListWidget()

        self.form_widget = MeetingFormWidget()

    def _layout_ui(self):
        layout = QVBoxLayout(self)

        # Header Layout
        header = QHBoxLayout()
        header.addWidget(self.title)
        header.addStretch()
        header.addWidget(self.add_new_btn)
        header.addWidget(self.filter_chk)

        layout.addLayout(header)
        layout.addWidget(self.view_list)
        layout.addWidget(self.form_widget)

    def _connect_method(self):
        self.add_new_btn.clicked.connect(self._on_add_new_clicked)
        self.filter_chk.stateChanged.connect(self._refresh_list)
        self.view_list.itemClicked.connect(self._on_item_selected)
        self.form_widget.on_save_requested.connect(self._on_save_request)

    def _on_add_new_clicked(self):
        """切換為建立模式"""
        self.active_meeting_id = None
        self.view_list.clearSelection()
        # 委派給元件處理 UI 變化
        self.form_widget.set_mode(is_create=True)

    def _on_item_selected(self, item):
        """切換為編輯模式"""
        m_id = item.data(Qt.ItemDataRole.UserRole)
        data = self.all_data.get(m_id)
        if not data:
            return

        self.active_meeting_id = m_id
        # 委派給元件處理 UI 變化與資料載入
        self.form_widget.set_mode(is_create=False)
        self.form_widget.load_data(data)

    def _on_save_request(self, meeting_schema: MeetingCreateSchema):
        """接收表單傳來的驗證後資料，執行 Service 邏輯"""
        if self._worker_ref and self._worker_ref.isRunning():
            return

        BottomBar.update_status.emit("🚀 處理中...", 0)
        self.form_widget.setEnabled(False)  # 鎖定表單

        self._worker_ref = self.service.save_meeting(
            self.active_meeting_id,
            meeting_schema,
            on_success=self._on_api_success,
            on_error=self._on_api_error,
        )

    def _on_api_success(self, result):
        BottomBar.update_status.emit("✅ 儲存成功！", 0)
        self.form_widget.setEnabled(True)
        self._refresh_list()

    def _on_api_error(self, err):
        BottomBar.update_status.emit(f"❌ 錯誤: {err}", 0)
        self.form_widget.setEnabled(True)

    def _refresh_list(self):
        """刷新清單並執行過濾邏輯"""
        self.view_list.clear()
        now = datetime.now()
        only_upcoming = self.filter_chk.isChecked()

        for m_id, info in self.all_data.items():
            start_time_str = info.get("start_time", "")
            try:
                m_start_dt = datetime.fromisoformat(
                    start_time_str.replace("Z", "+00:00")
                ).replace(tzinfo=None)
            except Exception:
                m_start_dt = now

            if only_upcoming and m_start_dt < now:
                continue

            item = QListWidgetItem(f"📅 {info.get('meeting_name', '未命名')}")
            item.setData(Qt.ItemDataRole.UserRole, m_id)
            if m_start_dt < now:
                item.setForeground(Qt.GlobalColor.gray)
                item.setText(item.text() + " (已結束)")
            self.view_list.addItem(item)


class MeetingFormWidget(QGroupBox):
    SPACING = 10
    on_save_requested = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.setEnabled(False)
        self.setFixedHeight(500)
        self.setMinimumWidth(800)

        self._init_ui()
        self._layout_ui()
        self._connect_signals()

    def _init_ui(self):
        self.meeting_name = CustomLineEdit(placeholder="請輸入會議名稱", width=400)

        # Left column
        self.meeting_type = fixed_width_height(QComboBox())
        self.meeting_type.addItems(MEETING_LAYOUT_OPTIONS.keys())  # type: ignore
        self.meeting_type.setMinimumWidth(200)

        self.meeting_url = CustomLineEdit(
            placeholder="請輸入會議連結", width=300, herizontal_stretch=True
        )
        self.room_id = CustomLineEdit(placeholder="請輸入會議識別 ID")
        self.meeting_password = CustomLineEdit(placeholder="請輸入會議密碼")
        self.repeat = QCheckBox("啟用重複排程")  # 加上 Label 比較清楚
        self.repeat_unit = CustomLineEdit(placeholder="請輸入重複週期(天)")
        self.repeat_end_date = fixed_width_height(QDateTimeEdit())
        self.repeat_end_date.setCalendarPopup(True)
        self.repeat_end_date.setDisplayFormat("yyyy/MM/dd")
        self.repeat_end_date.setDateTime(QDateTime.currentDateTime())

        # Right column
        self.meeting_layout = fixed_width_height(QComboBox())

        self.empty = QLabel("")
        self.empty.setFixedHeight(35)

        self.creator_name = CustomLineEdit(placeholder="請輸入建立者名稱")
        self.creator_email = CustomLineEdit(placeholder="請輸入建立者 Email")
        self.start_time = DateTimeInputGroup(0)
        self.end_time = DateTimeInputGroup(1)

        self.save_button = QPushButton("💾 提交變更")
        self.save_button.setMinimumHeight(45)
        self._update_meeting_layout(self.meeting_type.currentText())

    def _layout_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(ALIGNTOP | ALIGNLEFT)

        # meeting name
        name_w, name_l = create_form_block()
        name_l.addRow("會議名稱:", self.meeting_name)
        main_layout.addWidget(name_w)

        # Two columns area
        two_columns_widget = QWidget()
        two_columns_layout = QHBoxLayout(two_columns_widget)
        two_columns_layout.setContentsMargins(0, 0, 0, 0)
        two_columns_layout.setSpacing(self.SPACING)

        left_w, left_l = create_form_block()
        left_l.addRow("會議類型:", self.meeting_type)
        left_l.addRow("會議URL:", self.meeting_url)
        left_l.addRow("會議識別 ID:", self.room_id)
        left_l.addRow("會議密碼:", self.meeting_password)
        left_l.addRow("是否重複排程:", self.repeat)
        left_l.addRow("重複週期(天):", self.repeat_unit)
        left_l.addRow("結束日期:", self.repeat_end_date)

        right_w, right_l = create_form_block()
        right_l.addRow("會議佈局:", self.meeting_layout)
        right_l.addRow("", self.empty)
        right_l.addRow("建立者名稱:", self.creator_name)
        right_l.addRow("建立者 Email:", self.creator_email)
        right_l.addRow("起始時間:", self.start_time)
        right_l.addRow("結束時間:", self.end_time)

        two_columns_layout.addWidget(left_w, stretch=1)
        two_columns_layout.addWidget(right_w, stretch=1)

        main_layout.addWidget(two_columns_widget)
        main_layout.addWidget(self.save_button, alignment=ALIGNRIGHT)

    def _connect_signals(self):
        self.save_button.clicked.connect(self._handle_save)
        self.meeting_type.currentTextChanged.connect(self._update_meeting_layout)

    def set_mode(self, is_create: bool):
        """切換建立/編輯模式的 UI 狀態"""
        self.setEnabled(True)
        if is_create:
            self.save_button.setText("🚀 建立並提交排程")
            self.save_button.setStyleSheet(
                "background-color: #28a745; color: white; font-weight: bold;"
            )
            self._clear_form()
        else:
            self.save_button.setText("💾 儲存變更內容")
            self.save_button.setStyleSheet(
                "background-color: #0078D4; color: white; font-weight: bold;"
            )

    def load_data(self, data: dict):
        """將資料填入表單"""
        self.meeting_name.setText(data.get("meeting_name", ""))
        self.meeting_type.setCurrentText(data.get("meeting_type", "Webex"))

        self._update_meeting_layout(self.meeting_type.currentText())
        self.meeting_layout.setCurrentText(data.get("meeting_layout", ""))

        self.meeting_url.setText(data.get("meeting_url", ""))
        self.room_id.setText(data.get("room_id", ""))
        self.meeting_password.setText(data.get("meeting_password", ""))
        self.creator_name.setText(data.get("creator_name", ""))
        self.creator_email.setText(data.get("creator_email", ""))

        self.repeat.setChecked(str(data.get("repeat", "")).lower() == "true")
        self.repeat_unit.setText(str(data.get("repeat_unit", "0")))

        # 修正 2: 增加時間解析的安全性
        try:
            s_time_str = data.get("start_time", "")
            if s_time_str:
                s_dt = datetime.fromisoformat(
                    s_time_str.replace("Z", "+00:00")
                ).replace(tzinfo=None)
                self.start_time.set_datetime(s_dt)

            e_time_str = data.get("end_time", "")
            if e_time_str:
                e_dt = datetime.fromisoformat(
                    e_time_str.replace("Z", "+00:00")
                ).replace(tzinfo=None)
                self.end_time.set_datetime(e_dt)
        except ValueError:
            print("Warning: Date parsing failed in load_data")

        r_dt_str = data.get("repeat_end_date", "")
        if r_dt_str:
            # 處理可能帶有 Z 的 ISO 字串轉為 PyQt QDateTime
            clean_str = r_dt_str.replace("Z", "")
            r_qdt = QDateTime.fromString(clean_str, Qt.DateFormat.ISODate)
            if r_qdt.isValid():
                self.repeat_end_date.setDateTime(r_qdt)

    def _handle_save(self):
        """收集資料並發送訊號"""
        try:
            data = {}
            # 這裡假設你的 Schema 欄位名稱跟 Widget 變數名稱是一一對應的
            # 這是使用 getattr 的前提
            for field in MeetingCreateSchema.model_fields.keys():
                widget = getattr(self, field, None)
                if widget:
                    data[field] = get_widget_value(widget)

            # 驗證資料
            validated_schema = MeetingCreateSchema.model_validate(data)

            # 發送 Pydantic 物件 (這裡對應上面的 pyqtSignal(object))
            self.on_save_requested.emit(validated_schema)

        except ValidationError as e:
            # 優化錯誤顯示格式
            error_msg = "\n".join(
                [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]
            )
            QMessageBox.warning(self, "資料錯誤", f"請檢查以下欄位：\n{error_msg}")
        except ValueError as e:
            QMessageBox.warning(self, "格式錯誤", str(e))

    def _clear_form(self):
        """清空所有 UI 欄位"""
        self.meeting_name.clear()
        self.meeting_type.setCurrentIndex(0)
        self.meeting_url.clear()
        self.room_id.clear()
        self.meeting_password.clear()
        self.creator_name.clear()
        self.creator_email.clear()
        self.repeat.setChecked(False)
        self.repeat_unit.clear()
        self.repeat_end_date.setDateTime(QDateTime.currentDateTime())

        # 確保 DateTimeInputGroup 有 reset 方法，否則會報錯
        if hasattr(self.start_time, "reset"):
            self.start_time.reset()
        if hasattr(self.end_time, "reset"):
            self.end_time.reset()

    def _update_meeting_layout(self, selected_type: str):
        options = MEETING_LAYOUT_OPTIONS.get(selected_type, [])
        self.meeting_layout.clear()
        if options:
            self.meeting_layout.addItems(options)
            self.meeting_layout.setEnabled(True)
        else:
            self.meeting_layout.addItem("無可用佈局")
            self.meeting_layout.setEnabled(False)
