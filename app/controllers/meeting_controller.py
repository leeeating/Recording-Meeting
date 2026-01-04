from typing import List

from fastapi import APIRouter, Depends, status

from app.controllers.dependencies import get_meeting_service
from app.models.schemas import (
    MeetingCreateSchema,
    MeetingQuerySchema,
    MeetingResponseSchema,
)
from app.services.meeting_service import MeetingService

router = APIRouter(prefix="/meeting", tags=["Meetings"])


# ----- Create Endpoints -----
@router.post(
    "/",
    response_model=MeetingResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="創建新的會議，並自動生成 Task",
)
async def create_meeting_endpoint(
    meeting_data: MeetingCreateSchema,
    service: MeetingService = Depends(get_meeting_service),
) -> MeetingResponseSchema:
    return service.create_meeting_and_task(meeting_data)


# ----- Query Endpoints -----
@router.get(
    "/{meeting_id}",
    response_model=MeetingResponseSchema,
    summary="根據 ID 獲取會議詳情",
)
async def get_meeting_endpoint(
    meeting_id: int, service: MeetingService = Depends(get_meeting_service)
) -> MeetingResponseSchema:
    # 若找不到 ID，Service 拋出的 NotFoundError 會自動轉為 404 JSON
    return service.get_meeting_by_id(meeting_id)


@router.get(
    "/",
    response_model=List[MeetingResponseSchema],
    summary="獲取會議列表（含過濾和分頁）",
)
async def get_meetings(
    params: MeetingQuerySchema = Depends(),
    service: MeetingService = Depends(get_meeting_service),
) -> List[MeetingResponseSchema]:
    return service.get_meetings(params)


# ----- Update Endpoints -----
@router.patch(
    "/{meeting_id}",
    response_model=MeetingResponseSchema,
    summary="更新會議資訊（部分更新）",
)
async def update_meeting_endpoint(
    meeting_id: int,
    update_data: MeetingCreateSchema,
    service: MeetingService = Depends(get_meeting_service),
) -> MeetingResponseSchema:
    # 過濾未設定欄位
    return service.update_meeting(meeting_id, update_data)


# ----- Delete Endpoints -----
@router.delete(
    "/{meeting_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="刪除指定會議及所有關聯任務",
)
async def delete_meeting_endpoint(
    meeting_id: int, service: MeetingService = Depends(get_meeting_service)
):
    service.delete_meeting(meeting_id)
    return None
