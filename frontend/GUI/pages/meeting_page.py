import logging
from datetime import datetime, timedelta

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

from app.models.schemas import MeetingCreateSchema, MeetingResponseSchema
from frontend.services.api_client import ApiClient
from shared.config import config

from .base_page import BasePage
from .page_config import ALIGNLEFT, ALIGNRIGHT, ALIGNTOP, MEETING_LAYOUT_OPTIONS
from .utils import (
    CustomLineEdit,
    DateTimeInputGroup,
    EmptyLabel,
    create_form_block,
    fixed_width_height,
    get_widget_value,
)

logger = logging.getLogger(__name__)


class MeetingManagerPage(BasePage):
    def __init__(self, api_client: ApiClient):
        super().__init__()
        self.api_client = api_client
        self.meeting_list = {}
        self.active_meeting_id = None
        self._worker_ref = None

        self._init_ui()
        self._layout_ui()
        self._signal_connect()

        self._on_add_new_clicked()
        self._refresh_list()

    def _init_ui(self):
        self.title = QLabel("會議管理系統")
        self.title.setObjectName("header")
        self.refresh_btn = QPushButton("重新載入資料")
        self.add_new_btn = QPushButton("＋建立新會議")
        self.filter_chk = QCheckBox("僅顯示尚未開始的會議")
        self.view_list = QListWidget()
        self.form_widget = MeetingFormWidget()

    def _layout_ui(self):
        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        header.addWidget(self.title)
        header.addStretch()
        header.addWidget(self.refresh_btn)
        header.addWidget(self.add_new_btn)
        header.addWidget(self.filter_chk)

        layout.addLayout(header)
        layout.addWidget(self.view_list)
        layout.addWidget(self.form_widget)

    def _signal_connect(self):
        self.add_new_btn.clicked.connect(self._on_add_new_clicked)
        self.filter_chk.stateChanged.connect(self._update_list_data)
        self.view_list.itemClicked.connect(self._on_item_selected)
        self.form_widget.save_requested.connect(self._handle_save_request)
        self.refresh_btn.clicked.connect(self._refresh_list)

    def _on_add_new_clicked(self):
        self.active_meeting_id = None
        self.view_list.clearSelection()
        self.form_widget.set_mode(is_create=True)

    def _on_item_selected(self, item: QListWidgetItem):
        m_id = item.data(Qt.ItemDataRole.UserRole)
        data = self.meeting_list.get(m_id)
        if data:
            self.active_meeting_id = m_id
            self.form_widget.set_mode(is_create=False)
            self.form_widget.load_data(data)

    def _handle_save_request(self, meeting_schema: MeetingCreateSchema):
        """直接調用 Client 進行儲存，並使用 callback 刷新"""
        # update request
        if self.active_meeting_id:
            self.run_request(
                self.api_client.update_meeting,
                self.active_meeting_id,
                meeting_schema,
                name="更新會議",
                callback=self._refresh_list,
                lock_widget=self.form_widget,
            )

        # create request
        else:
            self.run_request(
                self.api_client.create_meeting,
                meeting_schema,
                name="建立新會議",
                callback=self._refresh_list,
                lock_widget=self.form_widget,
            )

    def _refresh_list(self, _=None):
        """獲取所有會議資料"""
        self.run_request(
            self.api_client.get_all_meetings,
            name="獲得資料清單",
            callback=self._on_fetch_data_loaded,
        )

    def _on_fetch_data_loaded(self, data_list: list[MeetingResponseSchema]):
        """處理 API 回傳的資料結構"""
        self.meeting_list = {str(m.id): m for m in data_list}
        self._update_list_data()

    def _update_list_data(self):
        """顯示資料到 UI"""
        self.view_list.clear()
        now = datetime.now()
        only_upcoming = self.filter_chk.isChecked()

        for m_id, m in self.meeting_list.items():
            m_start_dt = m.start_time.replace(tzinfo=None) if m.start_time else now

            if only_upcoming and m_start_dt < now:
                continue

            display_name = m.meeting_name or "未命名會議"

            item = QListWidgetItem(f"📅 {display_name}")
            item.setData(Qt.ItemDataRole.UserRole, m_id)

            if m_start_dt < now:
                item.setForeground(Qt.GlobalColor.gray)
                item.setText(item.text() + " (已結束)")

            self.view_list.addItem(item)


# ----------------------------------------------------------------------------


class MeetingFormWidget(QGroupBox):
    SPACING = 10
    save_requested = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.setEnabled(False)
        self.setFixedHeight(500)
        self.setMinimumWidth(800)

        self._init_ui()
        self._layout_ui()
        self._connect_signals()

    def _init_ui(self):
        """
        property name according to schema name
        """
        self.meeting_name = CustomLineEdit(placeholder="請輸入會議名稱", width=400)

        # Left column
        self.meeting_type = fixed_width_height(QComboBox())
        self.meeting_type.addItems(MEETING_LAYOUT_OPTIONS.keys())  # type: ignore
        self.meeting_type.setMinimumWidth(200)

        self.meeting_url = CustomLineEdit(
            placeholder="Optional", width=300, herizontal_stretch=True
        )
        self.room_id = CustomLineEdit(placeholder="Optional")
        self.meeting_password = CustomLineEdit(placeholder="Optional")
        self.repeat = QCheckBox("Optional")
        self.repeat_unit = CustomLineEdit(placeholder="Optional")
        self.repeat_end_date = fixed_width_height(QDateTimeEdit())
        self.repeat_end_date.setCalendarPopup(True)
        self.repeat_end_date.setDisplayFormat("yyyy/MM/dd")
        self.repeat_end_date.setDateTime(QDateTime.currentDateTime())

        # Right column
        self.meeting_layout = fixed_width_height(QComboBox())

        self.empty = EmptyLabel(height=35)

        self.creator_name = CustomLineEdit(placeholder="請輸入建立者名稱")
        # 保留變數資訊，刪除UI渲染
        self.creator_email = CustomLineEdit(placeholder="Optional")
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

        right_w, right_l = create_form_block()
        right_l.addRow("會議URL:", self.meeting_url)
        right_l.addRow("會議識別 ID:", self.room_id)
        right_l.addRow("會議密碼:", self.meeting_password)
        right_l.addRow("是否重複:", self.repeat)
        right_l.addRow("重複週期(天):", self.repeat_unit)
        right_l.addRow("結束日期\n(Optional):", self.repeat_end_date)

        left_w, left_l = create_form_block()
        left_l.addRow("會議類型:", self.meeting_type)
        left_l.addRow("會議佈局:", self.meeting_layout)
        left_l.addRow("建立者名稱:", self.creator_name)
        # left_l.addRow("建立者 Email:", self.creator_email)
        left_l.addRow("起始時間:", self.start_time)
        left_l.addRow("結束時間:", self.end_time)

        two_columns_layout.addWidget(left_w, stretch=1)
        two_columns_layout.addWidget(right_w, stretch=1)

        main_layout.addWidget(two_columns_widget)
        main_layout.addWidget(self.save_button, alignment=ALIGNRIGHT)

    def _connect_signals(self):
        self.save_button.clicked.connect(self._collect_date_and_emit_signal)
        self.meeting_type.currentTextChanged.connect(self._update_meeting_layout)
        self.start_time.changed.connect(self._sync_end_time)

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

    def load_data(self, data: MeetingResponseSchema):
        """
        將 Pydantic 物件資料填入表單
        """
        logger.info(f"表單載入會議資料: {data.meeting_name} (ID: {data.id})")

        # 基本文字欄位 (使用物件屬性，不再需要 .get)
        self.meeting_name.setText(data.meeting_name or "")
        self.meeting_url.setText(data.meeting_url or "")
        self.room_id.setText(data.room_id or "")
        self.meeting_password.setText(data.meeting_password or "")
        self.creator_name.setText(data.creator_name or "")
        self.creator_email.setText(data.creator_email or "")

        # 下拉選單與連動邏輯
        m_type = data.meeting_type or "Webex"
        self.meeting_type.setCurrentText(m_type)

        # 觸發佈局連動，再設定佈局值
        self._update_meeting_layout(m_type)
        self.meeting_layout.setCurrentText(data.meeting_layout or "")

        # 週期性與布林值 (Pydantic 已經保證 data.repeat 是 bool)
        self.repeat.setChecked(data.repeat)
        self.repeat_unit.setText(str(data.repeat_unit or "0"))

        # 時間處理：現在 data.start_time 已經是 datetime 物件了
        if data.start_time:
            self.start_time.set_datetime(data.start_time.replace(tzinfo=None))

        if data.end_time:
            self.end_time.set_datetime(data.end_time.replace(tzinfo=None))

        # 週期結束日期：處理 QDateTime 轉換
        if data.repeat_end_date:
            r_dt = data.repeat_end_date
            q_dt = QDateTime(r_dt.year, r_dt.month, r_dt.day, 0, 0)
            self.repeat_end_date.setDateTime(q_dt)
        else:
            self.repeat_end_date.setDateTime(QDateTime.currentDateTime())

    def _collect_date_and_emit_signal(self):
        """收集資料並發送訊號"""
        try:
            data = {}
            for field in MeetingCreateSchema.model_fields.keys():
                widget = getattr(self, field, None)
                if widget:
                    data[field] = get_widget_value(widget)

            if data["repeat_unit"] is None:
                data["repeat_unit"] = 0

            if data["creator_email"] is None:
                data["creator_email"] = config.DEFAULT_USER_EMAIL

            validated_schema = MeetingCreateSchema.model_validate(data)

            self.save_requested.emit(validated_schema)
            self._clear_form()

        except ValidationError as e:
            error_msg = "\n".join([f"{err['loc']}: {err['msg']}" for err in e.errors()])
            QMessageBox.warning(self, "資料錯誤", f"請檢查以下欄位：\n{error_msg}")

        except Exception as e:
            QMessageBox.warning(self, "格式錯誤", str(e))

    def _sync_end_time(self):
        """
        end time隨者start time改變
        """
        try:
            start_dt = self.start_time.get_datetime()

            new_end_dt = start_dt + timedelta(minutes=1)

            self.end_time.set_datetime(new_end_dt)

        except Exception as e:
            logger.warning(f"自動調整結束時間失敗: {e}")

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
