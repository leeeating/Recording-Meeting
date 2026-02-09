import logging
from datetime import datetime
from typing import List

from sqlalchemy import case, select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import NotFoundError
from app.models.meeting import MeetingORM
from app.models.schemas import (
    MeetingCreateSchema,
    MeetingQuerySchema,
    MeetingResponseSchema,
    MeetingUpdateSchema,
)
from shared.config import TAIPEI_TZ

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
        self,
        meeting_data: MeetingCreateSchema,
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

            tasks_id = [task.id for task in tasks]
            self.logger.info(
                f"Creating Tasks ID: {tasks_id} for Meeting ID {meeting.id})"
            )

            for task in tasks:
                self.task_service.add_job_to_scheduler(task_id=task.id)

        except Exception as e:
            self.logger.error(
                f"Failed to create Task & Job for Meeting [{meeting.meeting_name}]. Error: {e}"
            )
            raise

        return MeetingResponseSchema.model_validate(meeting)

    # ----- Query Methods -----
    def get_meeting_by_id(
        self,
        meeting_id: int,
    ) -> MeetingResponseSchema:
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

    def get_meetings(
        self,
        params: MeetingQuerySchema,
    ) -> List[MeetingResponseSchema]:
        """
        根據查詢參數獲取 Meeting 列表，支持分頁和排序。
        """
        now = datetime.now(tz=TAIPEI_TZ)

        stmt = select(MeetingORM)

        # 定義「是否尚未結束」的條件
        is_not_finished = case(
            ((MeetingORM.repeat.is_(True)) & (MeetingORM.repeat_end_date >= now), 0),
            ((MeetingORM.repeat.is_(False)) & (MeetingORM.end_time >= now), 0),
            else_=1,
        )

        stmt = stmt.order_by(
            # 第一優先級：未結束(0) 在前，已結束(1) 在後
            is_not_finished.asc(),
            # 第二優先級：處理「未結束」群組的正序 (asc)
            # 當符合未結束條件時，回傳時間值；否則回傳 NULL。
            # NULL 會被排在最後面，不影響此處的 asc 排序。
            case(
                (
                    (
                        (MeetingORM.repeat.is_(True))
                        & (MeetingORM.repeat_end_date >= now)
                    )
                    | ((MeetingORM.repeat.is_(False)) & (MeetingORM.end_time >= now)),
                    MeetingORM.start_time,
                )
            )
            .asc()
            .nullslast(),
            # 第三優先級：處理「已結束」群組的反序 (desc)
            # 邏輯同上，但針對已結束的資料回傳時間值，並套用 desc。
            case(
                (
                    ((MeetingORM.repeat.is_(True)) & (MeetingORM.repeat_end_date < now))
                    | ((MeetingORM.repeat.is_(False)) & (MeetingORM.end_time < now)),
                    MeetingORM.start_time,
                )
            )
            .desc()
            .nullslast(),
        )

        results = self.db.execute(stmt).scalars().all()
        return [MeetingResponseSchema.model_validate(meeting) for meeting in results]

    # ----- Update Methods -----
    def update_meeting(
        self,
        meeting_id: int,
        data: MeetingUpdateSchema,
    ) -> MeetingResponseSchema:
        meeting = self.db.query(MeetingORM).filter(MeetingORM.id == meeting_id).first()

        if not meeting:
            self.logger.error(f"Cannot update: Meeting ID {meeting_id} not found.")
            raise NotFoundError(detail=f"Meeting ID {meeting_id} not found.")

        updates_data = data.model_dump(exclude_unset=True)

        columns_with_time = [
            "start_time",
            "end_time",
            "repeat",
            "repeat_unit",
            "repeat_end_date",
        ]
        task_change = False
        for key, value in updates_data.items():
            if (key in columns_with_time) and (getattr(meeting, key) != value):
                task_change = True
            setattr(meeting, key, value)
        if task_change:
            self.task_service.update_task(meeting)

        try:
            self.db.commit()
            self.db.refresh(meeting)
            self.logger.info(f"會議 {meeting_id} 更新完成")

        except Exception as e:
            self.db.rollback()
            self.logger.error(f"資料庫更新失敗: {str(e)}")
            raise

        return MeetingResponseSchema.model_validate(meeting)

    # ----- Delete Methods -----
    def delete_meeting(
        self,
        meeting_id: int,
    ) -> MeetingResponseSchema:
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

            for deleted_task_id in [task.id for task in meeting.tasks]:
                self.task_service.remove_job_from_scheduler(deleted_task_id)

        except Exception as e:
            self.logger.error(f"Failed to delete Meeting ID {meeting_id}. Error: {e}")
            raise

        return MeetingResponseSchema.model_validate(meeting)
