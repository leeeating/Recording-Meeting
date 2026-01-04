from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import Depends
from sqlalchemy.orm import Session

# 引入核心配置和例外
from app.core.database import get_db
from app.core.scheduler import scheduler

# 引入服務層
from app.services.meeting_service import MeetingService
from app.services.task_service import TaskService


def get_scheduler_instance() -> BackgroundScheduler:
    return scheduler


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
