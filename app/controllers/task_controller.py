from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session, joinedload

from app.controllers.dependencies import get_task_service
from app.core.database import get_db
from app.core.scheduler import scheduler
from app.models import TaskORM
from app.models.schemas import (
    TaskQuerySchema,
    TaskResponseSchema,
)
from app.services.meeting_service import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])


# ----- Query Endpoints -----
@router.get(
    "/",
    response_model=List[TaskResponseSchema],
    summary="獲取任務列表（含過濾和分頁）",
)
async def get_tasks_endpoint(
    params: TaskQuerySchema = Depends(),
    service: TaskService = Depends(get_task_service),
):
    # 直接回傳結果，錯誤交給全域處理器
    return service.get_all_tasks(params)


@router.get(
    "/{task_id}",
    response_model=TaskResponseSchema,
    summary="根據 ID 獲取任務詳情",
)
async def get_task_endpoint(
    task_id: int, service: TaskService = Depends(get_task_service)
):
    return service.get_task_by_id(task_id)


# ----- Update Endpoints -----
@router.patch(
    "/{task_id}",
    response_model=TaskResponseSchema,
    summary="根據 ID 更新任務資訊",
)
async def update_task_endpoint(
    task_id: int,
    update_data: TaskQuerySchema,
    service: TaskService = Depends(get_task_service),
):
    # model_dump(exclude_unset=True) 確保只更新有傳入的欄位
    updates = update_data.model_dump(exclude_unset=True)
    return service.update_task(**updates)


# ----- Delete Endpoints -----
@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="根據 ID 刪除任務",
)
async def delete_task_endpoint(
    task_id: int, service: TaskService = Depends(get_task_service)
):
    service.delete_task(task_id)
    return None


@router.get("/scheduler/jobs")
async def list_jobs(db: Session = Depends(get_db)):
    # 這裡是在後端進程執行，所以能抓到真正的 jobs
    jobs = scheduler.get_jobs()
    result = []

    for job in jobs:
        task_id = int(job.id.split("_")[-1])
        task = (
            db.query(TaskORM)
            .options(joinedload(TaskORM.meeting))
            .filter(TaskORM.id == task_id)
            .first()
        )

        result.append(
            {
                "id": job.id,
                "name": task.meeting.meeting_name if task else "未知會議",
                "next_run_time": job.next_run_time.strftime("%Y-%m-%d %H:%M")
                if job.next_run_time
                else "已暫停",
            }
        )

    return result
