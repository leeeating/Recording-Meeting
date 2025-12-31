import logging
from typing import Callable

import requests
from PyQt6.QtCore import QThread, pyqtSignal
from requests.exceptions import RequestException

from app.models.schemas import MeetingCreateSchema

logger = logging.getLogger(__name__)


class ApiClient:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")
        self.timeout = 10
        self.meeting_router = f"{self.base_url}/meeting"
        self.task_router = f"{self.base_url}/tasks"

    def create_meeting(self, data: MeetingCreateSchema):
        """專門處理「創建會議」的網路通訊"""

        payload = data.model_dump(mode="json")

        try:
            response = requests.post(
                self.meeting_router,
                json=payload,
                timeout=self.timeout,
            )

            if response.status_code == 422:
                logger.warning("API Request Failed")

            response.raise_for_status()
            return response.json()

        except RequestException as e:
            raise Exception(f"API 連線異常: {str(e)}")

    def get_all_meetings(self):
        """專門處理「獲取所有會議」的網路通訊"""
        try:
            response = requests.get(self.meeting_router, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        except RequestException as e:
            raise Exception(f"API 連線異常: {str(e)}")

    def update_meeting(self, meeting_id: str, data: MeetingCreateSchema):
        """專門處理「更新會議」的網路通訊"""
        pass


class ApiWorker(QThread):
    """
    Create new thread to handle API requests without blocking the GUI.
    """

    success = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, api_func: Callable, *args, **kwargs):
        super().__init__()
        self.api_func: Callable = api_func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            # 開啟新線程執行API請求
            result = self.api_func(*self.args, **self.kwargs)
            self.success.emit(result)

        except Exception as e:
            self.error.emit(str(e))
