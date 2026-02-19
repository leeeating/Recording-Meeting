"""
錄影監控服務

功能：
1. 每 30 秒檢查 OBS 和會議平台的運行狀態
2. 自動重啟崩潰的應用程式
3. 發送告警郵件

架構：
- MonitorState: 追蹤當前任務的監控狀態（重啟次數、告警時間）
- MonitorService: 核心監控邏輯（進程檢查、重啟、告警）
- monitor_recording(): APScheduler 調用的入口函數

使用方式：
1. 在 start_recording() 成功後調用 scheduler.add_job(monitor_recording, ...)
2. 在 end_recording() 開頭調用 scheduler.remove_job(f"task_monitor_{task_id}")
3. 監控任務會自動處理崩潰和重啟

限制：
- OBS 只重啟一次（避免無限循環）
- 會議平台只重啟一次
- 5 分鐘內不重複發送相同告警
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import psutil
from sqlalchemy.orm import Session, joinedload

from app.core.database import database_engine
from app.models import TaskORM
from app.models.enums import TaskStatus
from app.recorder.obs_manager import OBSManager
from app.recorder.utils import action, kill_process
from app.recorder.webex_manager import WebexManager
from app.recorder.zoom_manager import ZoomManager
from shared.config import TAIPEI_TZ, config

logger = logging.getLogger(__name__)

# 進程名稱映射（複用 recorder.py 的定義）
PROCESS_MAP = {
    "ZOOM": "Zoom.exe",
    "WEBEX": "CiscoCollabHost.exe",
}


@dataclass
class MonitorState:
    """監控狀態追蹤"""

    obs_restart_attempted: bool = False  # 標記是否已嘗試重啟 OBS
    meeting_restart_attempted: bool = False  # 標記是否已嘗試重啟會議平台
    last_alert_time: Optional[datetime] = None  # 上次告警時間


class MonitorService:
    """錄影監控服務"""

    _state: Optional[MonitorState] = None
    _current_task_id: Optional[int] = None

    def __init__(self):
        self.obs_mgr = OBSManager()

    def get_state(self, task_id: int) -> MonitorState:
        """獲取或創建監控狀態（切換 task 時自動重置）"""
        if self._current_task_id != task_id or self._state is None:
            self._state = MonitorState()
            self._current_task_id = task_id
        return self._state

    def cleanup_state(self, task_id: int):
        """清理監控狀態"""
        if self._current_task_id == task_id:
            self._state = None
            self._current_task_id = None
            logger.debug(f"Task {task_id}: 監控狀態已清理")

    def is_process_running(self, process_name: str) -> bool:
        """檢查進程是否運行"""
        for proc in psutil.process_iter(["name"]):
            try:
                if proc.info["name"] == process_name:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

    def check_obs_recording_status(self) -> bool:
        """檢查 OBS 是否正在錄影"""
        try:
            self.obs_mgr.connect(retries=2, timeout=3)  # 快速檢查
            status = self.obs_mgr.client.get_record_status()
            return status.output_active
        except Exception as e:
            logger.debug(f"無法檢查 OBS 錄影狀態: {e}")
            return False

    def restart_obs(self, task: TaskORM) -> bool:
        """重啟 OBS 並恢復錄影"""
        meeting_type = task.meeting.meeting_type.upper()
        scene_name = (

            config.WEBEX_SCENE_NAME
            if meeting_type == "WEBEX"
            else config.ZOOM_SCENE_NAME
        )

        with action(f"重啟 OBS (Task {task.id})", logger):
            try:
                self.obs_mgr.launch_obs()
                time.sleep(1)
                self.obs_mgr.connect()
                time.sleep(1)
                self.obs_mgr.setup_obs_scene(scene_name=scene_name)

                if config.ENV == "prod":
                    self.obs_mgr.start_recording()

                if meeting_type == "WEBEX":
                    self.obs_mgr.setup_obs_window()

                logger.info(f"Task {task.id}: OBS 重啟成功")
                return True

            except Exception as e:
                logger.error(f"Task {task.id}: OBS 重啟失敗 - {str(e)}")
                return False

    def restart_meeting_platform(self, task: TaskORM) -> bool:
        """重啟會議平台並重新加入"""
        meeting_type = task.meeting.meeting_type.upper()
        process_name = PROCESS_MAP.get(meeting_type)

        if not process_name:
            logger.error(f"未知的會議類型: {meeting_type}")
            return False

        with action(f"重啟會議平台 (Task {task.id})", logger):
            try:
                # 先告警（因為可能卡在等待室）
                self.send_alert(
                    task.id,
                    f"會議平台 {meeting_type} 崩潰，正在嘗試重啟",
                )

                # 終止進程
                kill_process(process_name)
                time.sleep(2)

                # 重新建立管理器並加入會議
                meeting_info = {
                    "meeting_name": task.meeting.meeting_name,
                    "meeting_url": task.meeting.meeting_url,
                    "meeting_id": task.meeting.room_id,
                    "password": task.meeting.meeting_password,
                    "layout": task.meeting.meeting_layout.upper(),
                }

                if meeting_type == "ZOOM":
                    meeting_mgr = ZoomManager(**meeting_info)
                elif meeting_type == "WEBEX":
                    meeting_mgr = WebexManager(**meeting_info)
                else:
                    raise ValueError(f"不支援的會議類型: {meeting_type}")

                meeting_mgr.join_meeting_and_change_layout()

                logger.info(f"Task {task.id}: 會議平台重啟成功")
                return True

            except Exception as e:
                logger.error(f"Task {task.id}: 會議平台重啟失敗 - {str(e)}")
                return False

    def send_alert(
        self, task_id: int, message: str, force: bool = False
    ):
        """發送告警郵件（防重複）"""
        state = self.get_state(task_id)
        now = datetime.now(TAIPEI_TZ)

        # 防止 5 分鐘內重複告警（除非 force=True）
        if not force and state.last_alert_time:
            elapsed = (now - state.last_alert_time).total_seconds()
            if elapsed < 300:  # 5 分鐘
                logger.debug(
                    f"Task {task_id}: 跳過重複告警（距上次 {elapsed:.0f} 秒）"
                )
                return

        logger.critical(message, extra={"send_email": True})
        state.last_alert_time = now

    def handle_obs_crash(self, task: TaskORM) -> bool:
        """處理 OBS 崩潰"""
        state = self.get_state(task.id)

        # 只嘗試重啟一次
        if state.obs_restart_attempted:
            logger.error(f"Task {task.id}: OBS 已重啟過，不再嘗試")
            self.send_alert(
                task.id,
                f"Task {task.id} ({task.meeting.meeting_name}): OBS 重啟失敗，任務終止",
                force=True,
            )
            self.mark_task_failed(task)
            return False

        logger.warning(f"Task {task.id}: 檢測到 OBS 崩潰，嘗試重啟")
        state.obs_restart_attempted = True

        success = self.restart_obs(task)
        if not success:
            self.send_alert(
                task.id,
                f"Task {task.id} ({task.meeting.meeting_name}): OBS 重啟失敗",
                force=True,
            )
            self.mark_task_failed(task)

        return success

    def handle_meeting_crash(self, task: TaskORM) -> bool:
        """處理會議平台崩潰"""
        state = self.get_state(task.id)

        # 只嘗試重啟一次
        if state.meeting_restart_attempted:
            logger.error(f"Task {task.id}: 會議平台已重啟過，不再嘗試")
            return False

        logger.warning(f"Task {task.id}: 檢測到會議平台崩潰，嘗試重啟")
        state.meeting_restart_attempted = True

        return self.restart_meeting_platform(task)

    def mark_task_failed(self, task: TaskORM):
        """標記任務為失敗"""
        with Session(database_engine) as db:
            task_in_db = (
                db.query(TaskORM).filter(TaskORM.id == task.id).first()
            )
            if task_in_db:
                task_in_db.status = TaskStatus.FAILED
                db.commit()
                logger.info(f"Task {task.id}: 狀態已更新為 FAILED")


# 全局單例
monitor_service = MonitorService()


def monitor_recording(task_id: int):
    """
    監控錄影狀態（APScheduler 每 30 秒調用）
    """
    logger.debug(f"Task {task_id}: 開始監控檢查")

    with Session(database_engine) as db:
        task = (
            db.query(TaskORM)
            .options(joinedload(TaskORM.meeting))
            .filter(TaskORM.id == task_id)
            .first()
        )

        # 1. 檢查任務是否存在
        if not task:
            logger.error(f"Task {task_id} 不存在，停止監控")
            monitor_service.cleanup_state(task_id)
            return

        # 2. 檢查任務狀態
        if task.status != TaskStatus.RECORDING:
            logger.info(
                f"Task {task_id} 狀態不是 RECORDING（當前: {task.status}），停止監控"
            )
            monitor_service.cleanup_state(task_id)
            return

        meeting_type = task.meeting.meeting_type.upper()
        meeting_process = PROCESS_MAP.get(meeting_type)
        all_ok = True

        # 3. 檢查 OBS 進程
        if not monitor_service.is_process_running("obs64.exe"):
            logger.warning(f"Task {task_id}: OBS 進程不存在")
            if not monitor_service.handle_obs_crash(task):
                return
            all_ok = False

        # 4. 檢查 OBS 錄影狀態
        if all_ok and not monitor_service.check_obs_recording_status():
            logger.warning(f"Task {task_id}: OBS 未錄影")
            if not monitor_service.handle_obs_crash(task):
                return
            all_ok = False

        # 5. 檢查會議平台進程
        if all_ok and meeting_process:
            if not monitor_service.is_process_running(meeting_process):
                logger.warning(f"Task {task_id}: {meeting_type} 進程不存在")
                monitor_service.handle_meeting_crash(task)
                all_ok = False

        # 6. 記錄監控結果
        if all_ok:
            logger.debug(f"Task {task_id}: 監控正常 ✓")
        else:
            logger.info(f"Task {task_id}: 監控發現異常並已處理")
