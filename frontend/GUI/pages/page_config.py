from PyQt6.QtCore import Qt

ALIGNLEFT = Qt.AlignmentFlag.AlignLeft
ALIGNRIGHT = Qt.AlignmentFlag.AlignRight
ALIGNTOP = Qt.AlignmentFlag.AlignTop

MEETING_LAYOUT_OPTIONS = {
    "Webex": ["GRID", "STACKED", "SIDE_BY_SIDE"],
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
