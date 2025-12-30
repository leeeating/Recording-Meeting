from PyQt6.QtCore import QObject, pyqtSignal

from app.models.schemas import (
    MeetingCreateSchema,
    TaskQuerySchema,
)


class MeetingPageSignals(QObject):
    """用於管理會議頁面的輸入和輸出信號。"""

    save_requested = pyqtSignal(MeetingCreateSchema)


class TaskPageSignals(QObject):
    """用於管理任務頁面的輸入和輸出信號。"""

    query_requested = pyqtSignal(TaskQuerySchema)


class StatueBarBus(QObject):
    """
    用於發送狀態欄更新消息的信號總線。
    """

    update_status = pyqtSignal([str, int])  # message, duration (ms)


class UISignals(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.meeting_page = MeetingPageSignals()
        self.task_page = TaskPageSignals()


BUS = StatueBarBus()
