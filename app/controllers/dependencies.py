from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.meeting_service import MeetingService
from app.services.task_service import TaskService


def get_task_service(
    db: Session = Depends(get_db),
    # scheduler: BackgroundScheduler = Depends(get_scheduler_instance),
) -> TaskService:
    return TaskService(db=db)


# 會議服務依賴於 DB Session 和 TaskService
def get_meeting_service(
    db: Session = Depends(get_db),
    task_service: TaskService = Depends(get_task_service),
) -> MeetingService:
    return MeetingService(db=db, task_service=task_service)
