import logging

from sqlalchemy.orm import Session, joinedload

from app.core.database import database_engine
from app.core.exceptions import NotFoundError
from app.models import TaskORM
from app.models.enums import TaskStatus
from app.recorder.obs_manager import OBSManager
from app.recorder.webex_manager import WebexManager
from app.recorder.zoom_manager import ZoomManager

logger = logging.getLogger(__name__)
obs_mgr = OBSManager()

SCENE_NAME_MAP = {
    "WEBEX": "Webex_APP",
    "ZOOM": "Zoom_APP",
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

            if not (obs_mgr.launch_obs() and obs_mgr.connect()):
                # TODO: send email notification
                logger.error(
                    "無法啟動或連線到 OBS，取消錄影", extra={"send_email": True}
                )
                raise ConnectionError("無法啟動或連線到 OBS")

            meeting_type = task.meeting.meeting_type.upper()

            obs_mgr.setup_obs_scene(scene_name=SCENE_NAME_MAP[meeting_type])
            obs_mgr.start_recording()

            # ----- status update -----
            task.status = TaskStatus.RECORDING
            db.commit()
            logger.info(f"OBS 正常啟動且錄影中，Task {task_id}")
            # -------------------------

            meeting_name = task.meeting.meeting_name
            meeting_url = task.meeting.meeting_url
            meeting_id = task.meeting.room_id
            meeting_password = task.meeting.meeting_password
            layout = task.meeting.meeting_layout.upper()

            mgr_dict = {
                "meeting_name": meeting_name,
                "meeting_url": meeting_url,
                "meeting_id": meeting_id,
                "password": meeting_password,
                "layout": layout,
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


def end_recording(task_id: int):
    obs_mgr.stop_recording()
    obs_mgr._force_stop_obs()
    logger.info(f"OBS 錄影已停止，Task {task_id}")

    # ----- status update -----
    with Session(database_engine) as db:
        try:
            task = db.query(TaskORM).get(task_id)
            if not task:
                logger.error(
                    f"結束錄影時，找不到 Task {task_id}", extra={"send_email": True}
                )
                raise NotFoundError(f"找不到 Task {task_id}")

            task.status = TaskStatus.COMPLETED
            db.commit()

        except Exception as e:
            db.rollback()
            logger.error(
                f"Update task status failed (ID: {task_id}): {str(e)}", exc_info=True
            )
