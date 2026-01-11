import logging
from typing import Callable

import requests
from PyQt6.QtCore import QObject, QRunnable, pyqtSignal
from requests.exceptions import ConnectionError, HTTPError, Timeout

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

    # ----------- meeting page request -----------
    def get_all_meetings(self):
        try:
            response = requests.get(self.meeting_router, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return [MeetingResponseSchema.model_validate(item) for item in data]

        except Exception as e:
            self._handle_error(e)

    def create_meeting(self, data: MeetingCreateSchema):
        try:
            payload = data.model_dump(mode="json")
            response = requests.post(
                self.meeting_router, json=payload, timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            self._handle_error(e)

    def update_meeting(self, meeting_id: str, data: MeetingCreateSchema):
        try:
            url = f"{self.meeting_router}/{meeting_id}"
            payload = data.model_dump(mode="json")
            response = requests.patch(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            self._handle_error(e)

    # ----------- satus page -----------
    def get_backend_status(self):
        try:
            response = requests.get(self.base_url, timeout=self.timeout)
            response.raise_for_status()
            return True

        except Exception as e:
            self._handle_error(e)

    def get_scheduler_data(self):
        try:
            url = f"{self.task_router}/scheduler/jobs"
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            self._handle_error(e)

    # ----------- task page -----------
    def get_tasks(self):
        pass

    def _handle_error(self, e: Exception):
        if isinstance(e, ConnectionError):
            msg = "無法連線至伺服器，請檢查後端是否啟動。"

        elif isinstance(e, Timeout):
            msg = "連線逾時，伺服器反應過慢。"

        elif isinstance(e, HTTPError):
            try:
                detail = e.response.json().get("detail", str(e))
                msg = f"{detail}"
            except Exception:
                msg = f"伺服器回應錯誤 (HTTP {e.response.status_code})"

        else:
            msg = f"發生未預期錯誤：{str(e)}"

        logger.error(msg)
        raise Exception(msg)


# ---------------------------------------------------------------------------------


class WorkerSignals(QObject):
    success = pyqtSignal(object, str)
    error = pyqtSignal(str)
    finished = pyqtSignal()


class ApiWorker(QRunnable):
    """
    Create new thread to handle API requests without blocking the GUI.
    """

    def __init__(
        self,
        api_func: Callable,
        name: str,
        *args,
        **kwargs,
    ):
        super().__init__()
        self.api_func: Callable = api_func
        self.args = args
        self.kwargs = kwargs
        self.name = name
        self.signal = WorkerSignals()

    def run(self):
        logger.debug(f"開始執行背景任務: {self.name}")
        try:
            result = self.api_func(*self.args, **self.kwargs)

            success_msg = f"執行[{self.name}]成功 ^_^"
            self.signal.success.emit(result, success_msg)
            logger.info(success_msg)

        except Exception as e:
            error_detail = str(e)

            display_msg = f"執行[{self.name}]失敗 >_< ({error_detail})"

            logger.error(display_msg)
            self.signal.error.emit(display_msg)
