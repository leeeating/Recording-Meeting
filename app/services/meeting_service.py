import logging
from typing import List

from sqlalchemy import asc, desc
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import NotFoundError
from app.models.meeting import MeetingORM
from app.models.schemas import (
    MeetingCreateSchema,
    MeetingQuerySchema,
    MeetingResponseSchema,
)

from .task_service import TaskService

meeting_service_logger = logging.getLogger(__name__)


class MeetingService:
    """
    會議服務類別：處理 Meeting 的 CRUD，並協調 Task 的自動生成。
    """

    def __init__(self, db: Session, task_service: TaskService):
        self.db = db
        self.task_service = task_service
        self.logger = meeting_service_logger

    # ----- Create Methods -----
    def create_meeting_and_task(
        self, meeting_data: MeetingCreateSchema
    ) -> MeetingResponseSchema:
        """
        創建 Meeting 記錄，並自動觸發 Task 的創建與排程。
        """
        meeting = MeetingORM(**meeting_data.model_dump())

        # write meeting to DB
        try:
            self.db.add(meeting)
            self.db.flush()
            tasks = self.task_service.create_task(meeting=meeting)
            self.db.commit()

            self.logger.info(f"Meeting [{meeting.meeting_name}] create successfully.")

            for task in tasks:
                self.task_service.add_job_to_scheduler(task_id=task.id)

        except Exception as e:
            self.logger.error(
                f"Failed to create Task & Job for Meeting [{meeting.meeting_name}]. Error: {e}"
            )
            raise

        return MeetingResponseSchema.model_validate(meeting)

    # ----- Query Methods -----
    def get_meeting_by_id(self, meeting_id: int) -> MeetingResponseSchema:
        """
        根據 ID 獲取 Meeting 記錄，包含關聯的 Tasks。
        """
        meeting = (
            self.db.query(MeetingORM)
            .options(joinedload(MeetingORM.tasks))
            .filter(MeetingORM.id == meeting_id)
            .first()
        )

        if not meeting:
            self.logger.warning(f"Meeting ID {meeting_id} not found.")
            raise NotFoundError(detail=f"Meeting ID {meeting_id} not found.")

        return MeetingResponseSchema.model_validate(meeting)

    def get_meetings(self, params: MeetingQuerySchema) -> List[MeetingResponseSchema]:
        """
        根據查詢參數獲取 Meeting 列表，支持分頁和排序。
        """
        query = self.db.query(MeetingORM)

        sort_column = MeetingORM.start_time
        order_func = asc if params.order == "asc" else desc
        query = query.order_by(order_func(sort_column))

        meetings = query.offset(params.skip).limit(params.limit).all()
        return [MeetingResponseSchema.model_validate(meeting) for meeting in meetings]

    # ----- Update Methods -----
    def update_meeting(self, meeting_id: int, **kwargs) -> MeetingResponseSchema:
        meeting = self.db.query(MeetingORM).filter(MeetingORM.id == meeting_id).first()

        if not meeting:
            self.logger.error(f"Cannot update: Meeting ID {meeting_id} not found.")
            raise NotFoundError(detail=f"Meeting ID {meeting_id} not found.")

        for key, value in kwargs.items():
            if hasattr(meeting, key):
                current_value = getattr(meeting, key)

                if current_value != value:
                    setattr(meeting, key, value)
                    self.logger.info(
                        f"Updated Meeting ID {meeting_id}: set {key} to {value}"
                    )

        self.db.add(meeting)
        return MeetingResponseSchema.model_validate(meeting)

    # ----- Delete Methods -----
    def delete_meeting(self, meeting_id: int) -> MeetingResponseSchema:
        """
        刪除指定 ID 的 Meeting 記錄及其關聯的 Tasks。
        """
        meeting = self.db.query(MeetingORM).filter(MeetingORM.id == meeting_id).first()

        if not meeting:
            self.logger.error(f"Cannot delete: Meeting ID {meeting_id} not found.")
            raise NotFoundError(detail=f"Meeting ID {meeting_id} not found.")

        try:
            self.db.delete(meeting)
            self.logger.info(
                f"Deleted Meeting ID {meeting_id} and its associated tasks."
            )

        except Exception as e:
            self.logger.error(f"Failed to delete Meeting ID {meeting_id}. Error: {e}")
            raise

        return MeetingResponseSchema.model_validate(meeting)
