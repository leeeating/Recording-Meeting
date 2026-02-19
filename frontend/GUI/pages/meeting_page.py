import logging
from datetime import datetime, timedelta

from pydantic import ValidationError
from PyQt6.QtCore import QDateTime, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.models.schemas import (
    MeetingCreateSchema,
    MeetingResponseSchema,
    MeetingUpdateSchema,
)
from frontend.services.api_client import ApiClient
from shared.config import TAIPEI_TZ, config

from .base_page import BasePage
from .page_config import ALIGNLEFT, ALIGNTOP, MEETING_LAYOUT_OPTIONS
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
        self.current_page = 0
        self.page_size = 10

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
        self.prev_btn = QPushButton("< 上一頁")
        self.next_btn = QPushButton("下一頁 >")
        self.page_label = QLabel("第 1 頁")
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

        paging = QHBoxLayout()
        paging.addWidget(self.prev_btn)
        paging.addStretch()
        paging.addWidget(self.page_label)
        paging.addStretch()
        paging.addWidget(self.next_btn)
        layout.addLayout(paging)

        layout.addWidget(self.form_widget)

    def _signal_connect(self):
        self.add_new_btn.clicked.connect(self._on_add_new_clicked)
        self.filter_chk.stateChanged.connect(self._on_filter_changed)
        self.prev_btn.clicked.connect(self._go_prev_page)
        self.next_btn.clicked.connect(self._go_next_page)
        self.view_list.itemClicked.connect(self._on_item_selected)
        self.form_widget.save_requested.connect(self._handle_save_request)
        self.refresh_btn.clicked.connect(self._refresh_list)
        self.form_widget.delete_requested.connect(self._handle_delete_request)

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
        self.current_page = 0
        if not data_list:
            self.meeting_list = {}
            self._update_list_data()
            return

        self.meeting_list = {str(m.id): m for m in data_list}
        self._update_list_data()

    def _update_list_data(self):
        """顯示資料到 UI（含分頁）"""
        self.view_list.clear()
        now = datetime.now(tz=TAIPEI_TZ)
        only_upcoming = self.filter_chk.isChecked()

        # 收集所有符合過濾條件的項目
        filtered_items = []
        for m_id, meeting in self.meeting_list.items():
            correct_end_time = (
                meeting.repeat_end_date.replace(tzinfo=TAIPEI_TZ)
                if meeting.repeat
                else meeting.end_time
            )

            if only_upcoming:
                is_started = meeting.start_time < now
                is_expired = correct_end_time < now
                if is_started and is_expired:
                    continue

            filtered_items.append((m_id, meeting, correct_end_time))

        # 計算分頁
        total = len(filtered_items)
        total_pages = max(1, (total + self.page_size - 1) // self.page_size)
        self.current_page = min(self.current_page, total_pages - 1)

        start = self.current_page * self.page_size
        page_items = filtered_items[start : start + self.page_size]

        # 渲染當頁項目
        for m_id, meeting, correct_end_time in page_items:
            postfix = "(Repeat)" if meeting.repeat else ""
            display_name = f"{meeting.meeting_name} {postfix}"

            item = QListWidgetItem(f"📅 {display_name}")
            item.setData(Qt.ItemDataRole.UserRole, m_id)

            if correct_end_time < now:
                item.setForeground(Qt.GlobalColor.gray)
                item.setText(item.text() + "- 已結束")

            self.view_list.addItem(item)

        # 更新分頁控制
        self.page_label.setText(f"第 {self.current_page + 1} / {total_pages} 頁")
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page < total_pages - 1)

    def _go_prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._update_list_data()

    def _go_next_page(self):
        self.current_page += 1
        self._update_list_data()

    def _on_filter_changed(self):
        self.current_page = 0
        self._update_list_data()

    def _handle_delete_request(self):
        """處理刪除會議請求"""
        if not self.active_meeting_id:
            return

        confirm = QMessageBox.question(
            self,
            "刪除確認",
            "您確定要刪除這場會議嗎？\n這將同時刪除所有關聯任務。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if confirm == QMessageBox.StandardButton.Yes:
            self.run_request(
                self.api_client.delete_meeting,
                self.active_meeting_id,
                name="刪除會議",
                callback=self._on_delete_success,
                lock_widget=self.form_widget,
            )

    def _on_delete_success(self, _=None):
        """刪除成功後的處理"""
        self.active_meeting_id = None
        self.form_widget.set_mode(is_create=True)  # 切換回建立模式或清空
        self._refresh_list()


# ----------------------------------------------------------------------------


class MeetingFormWidget(QGroupBox):
    SPACING = 10
    save_requested = pyqtSignal(object)
    delete_requested = pyqtSignal()

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
        self.meeting_name = CustomLineEdit(placeholder="請輸入會議名稱", width=600)

        # Left column
        self.meeting_type = fixed_width_height(QComboBox())
        self.meeting_type.addItems(MEETING_LAYOUT_OPTIONS.keys())  # type: ignore
        self.meeting_type.setMinimumWidth(200)

        self.meeting_url = CustomLineEdit(
            placeholder="Optional", width=300, herizontal_stretch=True
        )
        self.room_id = CustomLineEdit(placeholder="Optional", width=300)
        self.meeting_password = CustomLineEdit(placeholder="Optional", width=300)
        self.repeat = QCheckBox("Optional")
        self.repeat_unit = CustomLineEdit(placeholder="Optional", width=300)
        self.repeat_end_date = fixed_width_height(QDateTimeEdit())
        self.repeat_end_date.setCalendarPopup(True)
        self.repeat_end_date.setDisplayFormat("yyyy/MM/dd")
        self.repeat_end_date.setDateTime(QDateTime.currentDateTime())

        # Right column
        self.meeting_layout = fixed_width_height(QComboBox())

        self.empty = EmptyLabel(height=35)

        self.creator_name = CustomLineEdit(placeholder="請輸入建立者名稱", width=300)
        # 保留變數資訊，刪除UI渲染
        self.creator_email = CustomLineEdit(placeholder="Optional", width=300)
        self.start_time = DateTimeInputGroup(0)
        self.end_time = DateTimeInputGroup(1)

        self.save_button = QPushButton("💾 提交變更")
        self.save_button.setMinimumHeight(45)

        self.delete_button = QPushButton("🗑️ 刪除會議")  # 新增
        self.delete_button.setStyleSheet(
            "background-color: #dc3545; color: white; font-weight: bold;"
        )
        self.delete_button.setMinimumHeight(45)
        self.delete_button.hide()  # 預設隱藏

        self.text_input_button = QPushButton("📋 文字輸入")
        self.text_input_button.setMinimumHeight(45)

        # Debug button: 設定開始時間為現在 + 30 秒（方便測試）
        self.debug_button = QPushButton("🐞 設定開始時間 +30秒")
        self.debug_button.setMinimumHeight(45)

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
        left_l.addRow("建立者 Email:", self.creator_email)
        left_l.addRow("起始時間:", self.start_time)
        left_l.addRow("結束時間:", self.end_time)

        two_columns_layout.addWidget(left_w, stretch=1)
        two_columns_layout.addWidget(right_w, stretch=1)

        main_layout.addWidget(two_columns_widget)

        # Buttons layout: debug + save
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.delete_button)
        btn_layout.addStretch()
        btn_layout.addWidget(self.text_input_button)
        btn_layout.addWidget(self.debug_button)
        btn_layout.addWidget(self.save_button)

        main_layout.addLayout(btn_layout)

    def _connect_signals(self):
        self.save_button.clicked.connect(self._collect_date_and_emit_signal)
        self.meeting_type.currentTextChanged.connect(self._update_meeting_layout)
        self.start_time.changed.connect(self._sync_end_time)
        self.text_input_button.clicked.connect(self._open_text_input_dialog)
        self.debug_button.clicked.connect(self._set_debug_start_time)
        self.delete_button.clicked.connect(self._on_delete_clicked)

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
            self.delete_button.show()

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
            for field in MeetingUpdateSchema.model_fields.keys():
                widget = getattr(self, field, None)
                if widget:
                    data[field] = get_widget_value(widget)

            if data["repeat_unit"] is None:
                data["repeat_unit"] = 0

            if data["creator_email"] is None:
                data["creator_email"] = config.DEFAULT_USER_EMAIL

            if data["creator_name"] is None:
                data["creator_name"] = "test"

            validated_schema = MeetingUpdateSchema.model_validate(data)

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

            new_end_dt = start_dt + timedelta(
                minutes=config.RECORDING_DURATION_IN_MINUTE
            )

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

    def _set_debug_start_time(self):
        """
        Debug helper: 設定 start_time 為現在 + 30 秒，並同步 end_time
        """

        try:
            now = datetime.now()
            new_start = now + timedelta(seconds=30)
            self.start_time.set_datetime(new_start)
            new_end = new_start + timedelta(minutes=config.RECORDING_DURATION_IN_MINUTE)
            self.end_time.set_datetime(new_end)

        except Exception as e:
            logger.warning(f"設定 debug 開始時間失敗: {e}")

    def _open_text_input_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("文字輸入")
        dialog.setMinimumSize(500, 400)

        layout = QVBoxLayout(dialog)

        hint = QLabel("hint: 沒有數值不用設定")
        layout.addWidget(hint)

        placeholder = """
            meeting_name: 週會\n
            meeting_type: Webex\n
            meeting_layout: Grid\n
            meeting_url: https://meet.webex.com/xxx\n
            room_id: 12345\n
            meeting_password: abc123\n
            repeat: true\n
            repeat_unit: 7\n
            creator_name: 王小明\n
            creator_email: test@email.com\n
            start_time: 2026-02-15 10:00\n
            end_time: 2026-02-15 11:00\n
        """

        text_edit = QPlainTextEdit()
        text_edit.setPlaceholderText(placeholder)
        text_edit.setStyleSheet("QPlainTextEdit { font-size: 18px; }")
        text_edit.setFixedHeight(500)
        layout.addWidget(text_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            text = text_edit.toPlainText().strip()
            if text:
                self._parse_and_fill_form(text)

    def _parse_and_fill_form(self, text: str):
        kv = {}
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            sep_idx = line.find(": ")
            if sep_idx == -1:
                continue
            key = line[:sep_idx].strip()
            value = line[sep_idx + 2 :].strip()
            kv[key] = value

        # 先填 meeting_type 以觸發 layout 選項更新
        if "meeting_type" in kv:
            self.meeting_type.setCurrentText(kv.pop("meeting_type"))

        for key, value in kv.items():
            widget = getattr(self, key, None)
            if widget is None:
                logger.warning(f"文字輸入：未知欄位 '{key}'，已跳過")
                continue

            if isinstance(widget, CustomLineEdit):
                widget.setText(value)
            elif isinstance(widget, QComboBox):
                widget.setCurrentText(value)
            elif isinstance(widget, QCheckBox):
                widget.setChecked(value.lower() in ("true", "1", "yes"))
            elif isinstance(widget, DateTimeInputGroup):
                try:
                    dt = datetime.strptime(value, "%Y-%m-%d %H:%M")
                    widget.set_datetime(dt)
                except ValueError:
                    logger.warning(f"文字輸入：無法解析時間 '{value}'，欄位 '{key}'")
            elif isinstance(widget, QDateTimeEdit):
                q_dt = QDateTime.fromString(value, "yyyy-MM-dd HH:mm")
                if q_dt.isValid():
                    widget.setDateTime(q_dt)
                else:
                    # 嘗試只有日期的格式
                    q_dt = QDateTime.fromString(value, "yyyy-MM-dd")
                    if q_dt.isValid():
                        widget.setDateTime(q_dt)
                    else:
                        logger.warning(
                            f"文字輸入：無法解析日期 '{value}'，欄位 '{key}'"
                        )

    def _on_delete_clicked(self):
        # 增加二次確認彈窗
        reply = QMessageBox.question(
            self,
            "確認刪除",
            "確定要刪除此會議嗎？此動作無法復原。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_requested.emit()
