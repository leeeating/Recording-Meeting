import logging
import time

from sqlalchemy.orm import Session, joinedload

from app.core.database import database_engine
from app.core.exceptions import NotFoundError
from app.models import TaskORM
from app.models.enums import TaskStatus
from app.recorder.obs_manager import OBSManager
from app.recorder.webex_manager import WebexManager
from app.recorder.zoom_manager import ZoomManager
from shared.config import config
from shared.logger import update_addressee

from .utils import action, kill_process

logger = logging.getLogger(__name__)
obs_mgr = OBSManager()

SCENE_NAME_MAP = {
    "WEBEX": config.WEBEX_SCENE_NAME,
    "ZOOM": config.ZOOM_SCENE_NAME,
}

PROCESS_MAP = {
    "ZOOM": "Zoom.exe",
    "WEBEX": "CiscoCollabHost.exe",
}


"""
每步驟都會有註解說明錯誤處理的等級
Critical Aciotn 會發送 Email
Error Aciotn 則只會在log中記錄，錄影會繼續，但輸出的畫面會有缺陷
"""


def start_recording(task_id: int):
    task = None
    with Session(database_engine) as db:
        task = (
            db.query(TaskORM)
            .options(joinedload(TaskORM.meeting))
            .filter(TaskORM.id == task_id)
            .first()
        )

        if not task:
            logger.critical(
                f"找不到 Task {task_id}，取消錄影", extra={"send_email": True}
            )
            raise NotFoundError(f"找不到 Task {task_id}")

        meeting_name = task.meeting.meeting_name
        meeting_type = task.meeting.meeting_type.upper()

        try:
            logger.debug(
                f"收到啟動指令，準備執行 Meeting Name: {task.meeting.meeting_name} Task ID: {task_id}"
            )

            update_addressee(task.meeting.creator_email)
            # update_addressee(config.ADDRESSEES_EMAIL)

            # Critical Action
            obs_mgr.launch_obs()
            time.sleep(1)

            # Critical Action
            obs_mgr.connect()
            time.sleep(1)

            # get default scene and recording
            scene_name = SCENE_NAME_MAP[meeting_type]

            # Critical Action
            obs_mgr.setup_obs_scene(scene_name=scene_name)

            # Critical Action
            logger.debug(f"{config.ENV}")
            if config.ENV == "prod":
                obs_mgr.start_recording()

            # ----- status update -----
            task.status = TaskStatus.RECORDING
            db.commit()
            logger.info("OBS 正常啟動且錄影中")
            # -------------------------

            meeting_info = {
                "meeting_name": task.meeting.meeting_name,
                "meeting_url": task.meeting.meeting_url,
                "meeting_id": task.meeting.room_id,
                "password": task.meeting.meeting_password,
                "layout": task.meeting.meeting_layout.upper(),
            }

            meeting_mgr = None
            if meeting_type == "ZOOM":
                meeting_mgr = ZoomManager(**meeting_info)

            elif meeting_type == "WEBEX":
                meeting_mgr = WebexManager(**meeting_info)

            else:
                logger.error(
                    "OBS正常啟動，但Meeting Menager初始化失敗",
                    extra={"send_email": True},
                )
                raise ValueError("Meeting Manager is None")

            # multiple action
            meeting_mgr.join_meeting_and_change_layout()

            # Error Action
            if meeting_type == "WEBEX":
                obs_mgr.setup_obs_window()

        except Exception as e:
            db.rollback()
            logger.critical(
                f"執行 start_recording 失敗 (Meeting Name: {meeting_name}, Task ID: {task_id}): {str(e)}",
                extra={
                    "send_email": True,
                    "meeting_name": meeting_name,
                    "meeting_type": meeting_type,
                },
            )

            task.status = TaskStatus.FAILED
            db.commit()


def end_recording(task_id: int):
    task = None
    with Session(database_engine) as db:
        task = (
            db.query(TaskORM)
            .options(joinedload(TaskORM.meeting))
            .filter(TaskORM.id == task_id)
            .first()
        )
        if not task:
            logger.error(
                f"結束錄影時，找不到 Task ID {task_id}",
            )
            raise NotFoundError(f"找不到 Task {task_id}")

        meetig_name = task.meeting.meeting_name

        try:
            obs_mgr.connect()
            time.sleep(1)

            obs_mgr.stop_recording()
            time.sleep(1)

            obs_mgr.disconnect()

            obs_mgr.kill_obs_process_by_taskkill()
            time.sleep(3)

            logger.info(f"OBS 錄影已停止，Meeting Nname: {meetig_name}, Task {task_id}")

            meeting_type = task.meeting.meeting_type.upper()

            kill_meeting_process(meeting_type)

            # 4. 更新任務狀態為完成
            if task.status == TaskStatus.UPCOMING:
                task.status = TaskStatus.COMPLETED
                db.commit()
                logger.info(
                    f"Meeting: {meetig_name}, Task ID {task_id} 錄影成功並已完整關閉相關程式"
                )

        except Exception as e:
            db.rollback()
            logger.critical(
                f"執行 end_recording 失敗 (Meeting: {meetig_name}, Task ID: {task_id}): {str(e)}",
                extra={"send_email": True},
            )

            task.status = TaskStatus.FAILED
            db.commit()


def kill_meeting_process(meeting_type: str | None):
    if meeting_type is None:
        logger.warning("Invalid meeting type. Must be either 'ZOOM' or 'WEBEX'.")
        return

    with action(f"關閉{meeting_type}", logger):
        Pname = PROCESS_MAP.get(meeting_type)
        kill_process(Pname)
