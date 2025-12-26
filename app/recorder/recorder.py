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

from .utils import kill_process, action

logger = logging.getLogger(__name__)
obs_mgr = OBSManager()

SCENE_NAME_MAP = {
    "WEBEX": "WEBEX_APP",
    "ZOOM": "ZOOM_APP",
}


def start_recording(task_id: int):
    logger.debug(f"收到啟動指令，準備執行 Task ID: {task_id}")

    task = None
    with Session(database_engine) as db:
        try:
            task = (
                db.query(TaskORM)
                .options(joinedload(TaskORM.meeting))
                .filter(TaskORM.id == task_id)
                .first()
            )

            if not task:
                # TODO: send email notification
                logger.error(
                    f"找不到 Task {task_id}，取消錄影", extra={"send_email": True}
                )
                raise NotFoundError(f"找不到 Task {task_id}")

            obs_mgr.kill_obs_process()
            time.sleep(1)

            obs_mgr.launch_obs()
            time.sleep(1)

            obs_mgr.connect()
            time.sleep(1)

            # get default scene and recording
            meeting_type = task.meeting.meeting_type.upper()
            obs_mgr.setup_obs_scene(scene_name=SCENE_NAME_MAP[meeting_type])
            obs_mgr.start_recording()
            # uncomment for testing launch and kill obs
            # raise

            # ----- status update -----
            task.status = TaskStatus.RECORDING
            db.commit()
            logger.info(f"OBS 正常啟動且錄影中，Task {task_id}")
            # -------------------------

            mgr_dict = {
                "meeting_name": task.meeting.meeting_name,
                "meeting_url": task.meeting.meeting_url,
                "meeting_id": task.meeting.room_id,
                "password": task.meeting.meeting_password,
                "layout": task.meeting.meeting_layout.upper(),
            }

            meeting_mgr = None
            if meeting_type == "ZOOM":
                meeting_mgr = ZoomManager(**mgr_dict)

            elif meeting_type == "WEBEX":
                meeting_mgr = WebexManager(**mgr_dict)

            else:
                # TODO: send email
                logger.error("Meeting Manager is None", extra={"send_email": True})
                raise ValueError("Meeting Manager is None")

            meeting_mgr.join_meeting_and_change_layout()

        except Exception as e:
            db.rollback()
            logger.error(
                f"執行 start_recording 失敗 (ID: {task_id}): {str(e)}",
                exc_info=True,
                extra={"send_email": True},
            )
            if task:
                task.status = TaskStatus.FAILED
                db.commit()
            raise e


def end_recording(task_id: int):
    with Session(database_engine) as db:
        try:
            task = (
                db.query(TaskORM)
                .options(joinedload(TaskORM.meeting))
                .filter(TaskORM.id == task_id)
                .first()
            )

            if not task:
                logger.error(f"結束錄影時，找不到 Task {task_id}", extra={"send_email": True})
                raise NotFoundError(f"找不到 Task {task_id}")

            obs_mgr.connect()
            time.sleep(1)
            obs_mgr.stop_recording()
            time.sleep(1)
            obs_mgr.kill_obs_process()
            time.sleep(1)
            logger.info(f"OBS 錄影已停止，Task {task_id}")

            meeting_type = task.meeting.meeting_type.upper()
            
            PROCESS_MAP = {
                "ZOOM": "Zoom.exe",
                "WEBEX": "CiscoCollabHost.exe"
            }

            p_name = PROCESS_MAP.get(meeting_type)
            
            with action(f"關閉 {meeting_type} 會議程式", logger):
                if p_name:
                    kill_process(p_name, logger)
                    logger.info(f"已要求關閉進程: {p_name}")
                else:
                    logger.warning(f"未定義的會議類型 {meeting_type}，無法自動關閉進程")

            # 4. 更新任務狀態為完成
            task.status = TaskStatus.COMPLETED
            db.commit()
            logger.info(f"Task {task_id} 錄影成功並已完整關閉相關程式")

        except Exception as e:
            db.rollback()
            logger.error(
                f"執行 end_recording 失敗 (ID: {task_id}): {str(e)}", 
                exc_info=True,
                extra={"send_email": True}
            )
            raise e