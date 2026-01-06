import logging
from typing import Callable

import requests
from PyQt6.QtCore import QObject, QRunnable, pyqtSignal
from requests.exceptions import RequestException

from app.core.scheduler import scheduler
from app.models.schemas import MeetingCreateSchema, MeetingResponseSchema

logger = logging.getLogger(__name__)


class ApiClient:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")
        self.timeout = 10
        self.meeting_router = f"{self.base_url}/meeting"
        self.task_router = f"{self.base_url}/tasks"
        self.schduler = scheduler

    def create_meeting(self, data: MeetingCreateSchema):
        """專門處理「創建會議」的網路通訊"""
        payload = data.model_dump(mode="json")
        logger.info(f"嘗試建立會議: {payload.get('meeting_name', 'N/A')}")

        try:
            response = requests.post(
                self.meeting_router,
                json=payload,
                timeout=self.timeout,
            )

            if not response.ok:
                logger.error(
                    f"建立會議失敗 | Status: {response.status_code} | Response: {response.text}"
                )
                response.raise_for_status()

            logger.info("會議建立成功")
            return response.json()

        except RequestException as e:
            logger.error(f"建立會議時發生網路異常: {str(e)}")
            raise

    def get_all_meetings(self):
        """專門處理「獲取所有會議」的網路通訊"""
        logger.debug("開始獲取會議清單...")

        try:
            response = requests.get(self.meeting_router, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            meetings = [MeetingResponseSchema.model_validate(item) for item in data]
            logger.debug(f"成功獲取清單，共 {len(meetings)} 筆資料")
            return meetings

        except RequestException as e:
            logger.warning(f"獲取會議清單失敗: {str(e)}")
            return []

    def update_meeting(self, meeting_id: str, data: MeetingCreateSchema):
        """專門處理「更新會議」的網路通訊"""
        url = f"{self.meeting_router}/{meeting_id}"
        payload = data.model_dump(mode="json")
        logger.debug("開始更新會議...")

        try:
            response = requests.patch(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        except RequestException as e:
            logger.error(f"更新連線異常 | ID: {meeting_id} | {str(e)}")
            raise Exception(f"無法連線至伺服器進行更新 (ID: {meeting_id})") from e

    def get_backend_status(self):
        """專門處理「獲取排程器狀態」的網路通訊"""
        try:
            response = requests.get(self.meeting_router, timeout=self.timeout)
            response.raise_for_status()
            return response.status_code == 200

        except Exception:
            logger.warning("API Request Failed")
            return False

    def get_scheduler_data(self):
        """修正：透過網路 API 獲取排程，而不是直接讀取物件"""
        logger.debug("從伺服器獲取排程資料...")
        try:
            url = f"{self.task_router}/scheduler/jobs"
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"獲取排程資料失敗: {e}")
            return []


class WorkerSignals(QObject):
    success = pyqtSignal(object)
    error = pyqtSignal(str)
    finished = pyqtSignal()


class ApiWorker(QRunnable):
    """
    Create new thread to handle API requests without blocking the GUI.
    """

    def __init__(self, api_func: Callable, *args, **kwargs):
        super().__init__()
        self.api_func: Callable = api_func
        self.args = args
        self.kwargs = kwargs
        self.signal = WorkerSignals()
        self.func_name = getattr(api_func, "__name__", "UnknownFunc")

    def run(self):
        logger.debug(f"開始執行背景任務: {self.func_name}")
        try:
            result = self.api_func(*self.args, **self.kwargs)
            logger.debug(f"任務執行成功: {self.func_name}")
            self.signal.success.emit(result)

        except Exception as e:
            logger.exception(f"背景任務拋出異常 ({self.func_name})")
            self.signal.error.emit(str(e))
