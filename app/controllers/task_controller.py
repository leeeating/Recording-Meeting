from fastapi import APIRouter, Depends, status
from typing import List

from app.services.meeting_service import TaskService
from app.models.schemas import (
    TaskQuerySchema,
    TaskResponseSchema,
)
from app.controllers.dependencies import get_task_service

# 這裡維持 prefix="/tasks"，但在 main.py 註冊時請注意不要重複前綴
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
    return service.update_task(task_id, **updates)


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
