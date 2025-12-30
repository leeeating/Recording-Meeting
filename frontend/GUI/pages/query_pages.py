from PyQt6.QtCore import QDateTime, Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

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
    def __init__(self, data_source=MOCK_MEETINGS_DATA):
        super().__init__()
        self.all_data = data_source
        self.active_meeting_id = None

        self._create_widgets()
        self._setup_layout()
        self._connect_signals()
        self._refresh_list()

    def _create_widgets(self):
        """創建 UI 元件"""
        # 1. 上方清單
        self.view_list = QListWidget()
        self.view_list.setFont(QFont("Microsoft JhengHei", 11))
        self.view_list.setMinimumHeight(150)

        # 2. 下方編輯區
        self.edit_group = QGroupBox("會議詳細資訊編輯")

        # 會議名稱 (滿版)
        self.name_edit = QLineEdit()
        self.name_edit.setFixedHeight(30)

        # 左側欄位
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Webex", "Zoom", "Teams"])
        self.url_edit = QLineEdit()
        self.room_id_edit = QLineEdit()
        self.pwd_edit = QLineEdit()
        self.repeat_chk = QCheckBox("是否重複排程")
        self.repeat_unit_edit = QLineEdit()
        self.repeat_end_date = QDateEdit()
        self.repeat_end_date.setCalendarPopup(True)

        # 右側欄位
        self.layout_combo = QComboBox()
        self.layout_combo.addItems(["網格", "堆疊", "側邊欄"])
        self.creator_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_time = QTimeEdit()
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_time = QTimeEdit()

        # 儲存按鈕
        self.save_btn = QPushButton("儲存變更")
        self.save_btn.setFixedHeight(40)
        self.save_btn.setStyleSheet(
            "background-color: #0078D4; color: white; font-weight: bold; border-radius: 2px;"
        )

    def _make_label(self, text):
        """輔助方法：創建固定寬度且右對齊的標籤"""
        label = QLabel(text)
        label.setFixedWidth(100)  # 統一調整標籤寬度
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return label

    def _setup_layout(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        main_layout.addWidget(QLabel("會議清單："))
        main_layout.addWidget(self.view_list)

        # --- 編輯群組內部的佈局 ---
        edit_v_layout = QVBoxLayout(self.edit_group)
        edit_v_layout.setContentsMargins(15, 20, 15, 15)
        edit_v_layout.setSpacing(12)

        # 1. 滿版的會議名稱列
        name_row = QHBoxLayout()
        name_row.addWidget(self._make_label("會議名稱："))
        name_row.addWidget(self.name_edit)
        edit_v_layout.addLayout(name_row)

        # 2. 雙欄位主要區域
        cols_container = QHBoxLayout()
        cols_container.setSpacing(30)  # 左右兩欄之間的間距

        # 左欄 (Left Column)
        left_form = QFormLayout()
        left_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        left_form.setHorizontalSpacing(15)
        left_form.addRow(self._make_label("會議類型："), self.type_combo)
        left_form.addRow(self._make_label("會議連結："), self.url_edit)
        left_form.addRow(self._make_label("會議識別 ID："), self.room_id_edit)
        left_form.addRow(self._make_label("會議密碼："), self.pwd_edit)
        left_form.addRow(self._make_label(" "), self.repeat_chk)
        left_form.addRow(self._make_label("重複週期(天)："), self.repeat_unit_edit)
        left_form.addRow(self._make_label("重複結束日期："), self.repeat_end_date)

        # 右欄 (Right Column)
        right_form = QFormLayout()
        right_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        right_form.setHorizontalSpacing(15)
        right_form.addRow(self._make_label("會議佈局："), self.layout_combo)
        right_form.addRow(self._make_label("建立者名稱："), self.creator_edit)
        right_form.addRow(self._make_label("建立者 Email："), self.email_edit)

        # 起始時間：日期與時間並列
        start_row = QHBoxLayout()
        start_row.addWidget(self.start_date)
        start_row.addWidget(self.start_time)
        right_form.addRow(self._make_label("起始時間："), start_row)

        # 結束時間：日期與時間並列
        end_row = QHBoxLayout()
        end_row.addWidget(self.end_date)
        end_row.addWidget(self.end_time)
        right_form.addRow(self._make_label("結束時間："), end_row)

        cols_container.addLayout(left_form)
        cols_container.addLayout(right_form)

        edit_v_layout.addLayout(cols_container)

        # 3. 按鈕區域 (確保按鈕下方有適當邊距)
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(100, 10, 0, 0)  # 讓按鈕對齊右側欄位的起始位置
        btn_layout.addWidget(self.save_btn)
        edit_v_layout.addLayout(btn_layout)

        main_layout.addWidget(self.edit_group)

    def _connect_signals(self):
        self.view_list.itemClicked.connect(self._on_item_selected)
        self.save_btn.clicked.connect(self._on_save_clicked)

    def _refresh_list(self):
        self.view_list.clear()
        for m_id, info in self.all_data.items():
            item = QListWidgetItem(f"📅 {info['meeting_name']}")
            item.setData(Qt.ItemDataRole.UserRole, m_id)
            self.view_list.addItem(item)
        self.edit_group.setEnabled(False)

    def _on_item_selected(self, item):
        m_id = item.data(Qt.ItemDataRole.UserRole)
        data = self.all_data.get(m_id)
        if not data:
            return

        self.active_meeting_id = m_id
        self.edit_group.setEnabled(True)
        self.name_edit.setText(data["meeting_name"])
        self.type_combo.setCurrentText(data["meeting_type"])
        self.url_edit.setText(data["meeting_url"])
        self.room_id_edit.setText(data["room_id"])
        self.pwd_edit.setText(data["meeting_password"])
        self.layout_combo.setCurrentText(data["meeting_layout"])
        self.creator_edit.setText(data["creator_name"])
        self.email_edit.setText(data["creator_email"])
        self.repeat_chk.setChecked(data["repeat"].lower() == "true")
        self.repeat_unit_edit.setText(str(data["repeat_unit"]))

        # 時間載入邏輯
        start_dt = QDateTime.fromString(data["start_time"], Qt.DateFormat.ISODate)
        self.start_date.setDate(start_dt.date())
        self.start_time.setTime(start_dt.time())
        end_dt = QDateTime.fromString(data["end_time"], Qt.DateFormat.ISODate)
        self.end_date.setDate(end_dt.date())
        self.end_time.setTime(end_dt.time())
        repeat_dt = QDateTime.fromString(data["repeat_end_date"], Qt.DateFormat.ISODate)
        self.repeat_end_date.setDate(repeat_dt.date())

    def _on_save_clicked(self):
        if not self.active_meeting_id:
            return
        # 資料寫回邏輯 (略，與前版一致)
        QMessageBox.information(self, "成功", "會議資料已更新")
        self._refresh_list()
