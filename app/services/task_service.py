import logging
from datetime import datetime, timedelta
from typing import List

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.orm.query import Query
from app.core.exceptions import NotFoundError, SchedulingError
from app.core.scheduler import scheduler
from app.models import MeetingORM, TaskORM
from app.models.enums import TaskStatus
from app.models.schemas import TaskQuerySchema, TaskResponseSchema
from app.recorder.recorder import end_recording, start_recording
from shared.config import TAIPEI_TZ

task_service_logger = logging.getLogger(__name__)


class TaskService:
    """
    任務服務類別：處理 Task 數據的持久化、排程和查詢。
    """

    def __init__(self, db: Session):
        self.db = db
        self.scheduler = scheduler
        self.logger = task_service_logger

    def _get_base_query(self) -> Query[TaskORM]:
        return self.db.query(TaskORM).options(joinedload(TaskORM.meeting))

    # ----- Insert and Schedule Methods -----
    def create_task(
        self,
        meeting: MeetingORM,
    ) -> List[TaskORM]:
        """
        根據 Meeting ORM 實例，創建一個或多個 Task 記錄。
        這是 MeetingService 協調 TaskService 的入口點。
        """

        execute_time = self._calculate_execute_time(meeting)
        created_tasks: list[TaskORM] = []

        for start_dt, end_dt in execute_time:
            task_instance = TaskORM(
                meeting_id=meeting.id,
                status=TaskStatus.UPCOMING,
                start_time=start_dt,
                end_time=end_dt,
            )
            self.db.add(task_instance)
            created_tasks.append(task_instance)

        self.db.flush()
        return created_tasks

    # ----- Query Methods -----
    def get_all_tasks(
        self,
        params: TaskQuerySchema,
    ) -> List[TaskResponseSchema]:
        query = self._get_base_query()

        # filtering
        if params.status:
            query = query.filter(TaskORM.status == params.status)

        # 在 get_all_tasks 方法中加入時間過濾
        if params.start_time_ge:
            query = query.filter(TaskORM.start_time >= params.start_time_ge)

        if params.end_time_le:
            query = query.filter(TaskORM.end_time <= params.end_time_le)

        # pagination
        tasks = (
            query.order_by(TaskORM.start_time.asc())
            .offset(params.skip)
            .limit(params.limit)
            .all()
        )

        return [TaskResponseSchema.model_validate(task) for task in tasks]

    def get_task_by_id(
        self,
        task_id: int,
    ) -> TaskResponseSchema:
        task = self._get_base_query().filter(TaskORM.id == task_id).first()

        if not task:
            self.logger.warning(f"Task ID {task_id} not found.")
            raise NotFoundError(detail=f"Task ID {task_id} not found.")

        return TaskResponseSchema.model_validate(task)

    # ----- Update Methods -----
    def update_task(
        self,
        meeting: MeetingORM,
    ):
        """
        如果meeting中與時間有關的欄位更動，再更新Task資料
        """
        tasks = (
            self.db.query(TaskORM)
            .filter(
                TaskORM.meeting_id == meeting.id, TaskORM.status == TaskStatus.UPCOMING
            )
            .all()
        )

        if not tasks:
            self.logger.error(f"Unable to update task for Meeting ID {meeting.id}.")
            raise NotFoundError("Unable to update task for Meeting ID")

        for task in tasks:
            self.delete_task(task.id)

        tasks = self.create_task(meeting)

        for task in tasks:
            self.add_job_to_scheduler(task_id=task.id)

    def update_task_status(
        self,
        task_id: int,
        new_status: TaskStatus,
    ) -> TaskResponseSchema:
        """
        手動更新指定 Task 的狀態。
        """
        task = self.db.query(TaskORM).filter(TaskORM.id == task_id).first()

        if not task:
            self.logger.error(f"Cannot update status: Task ID {task_id} not found.")
            raise NotFoundError(detail=f"Task ID {task_id} not found.")

        if task.status != new_status:
            old_status = task.status
            task.status = new_status
            self.logger.info(
                f"Updated Task ID {task_id} status from {old_status} to {new_status}"
            )

        return TaskResponseSchema.model_validate(task)

    # ----- Delete Methods -----
    def delete_task(
        self,
        task_id: int,
    ):
        """
        刪除尚未執行的任務，確保不會更動到以前的任務狀態。
        """
        task = self.db.query(TaskORM).filter(TaskORM.id == task_id).first()

        if not task:
            self.logger.error(f"Cannot delete: Task ID {task_id} not found.")
            raise NotFoundError(detail=f"Task ID {task_id} not found.")

        try:
            self.db.delete(task)
            self.remove_job_from_scheduler(task_id=task_id)
            self.logger.info(f"Deleted Task ID {task_id} from database.")

        except Exception as e:
            self.logger.error(
                f"Failed to delete Task ID {task_id} or remove scheduled jobs. Error: {e}"
            )
            raise

        return

    # -----------------------------------------------------------------------------

    def remove_job_from_scheduler(
        self,
        task_id: int,
    ):
        """
        從排程器中移除指定 Task ID 的 Start 和 End Job，並容忍 Job 不存在。
        """
        start_job_id = f"task_start_{task_id}"
        end_job_id = f"task_end_{task_id}"

        for job_id in [start_job_id, end_job_id]:
            try:
                # 檢查 Job 是否存在，若存在則移除
                if self.scheduler.get_job(job_id):
                    self.scheduler.remove_job(job_id)
                    self.logger.info(f"Successfully removed job ID: {job_id}.")

            except Exception as e:
                # 這裡應只捕獲 apscheduler 內部錯誤 (如 Job 仍在運行)
                self.logger.warning(
                    f"Failed to cleanly remove job ID {job_id} from scheduler. Error: {e}"
                )

    def add_job_to_scheduler(
        self,
        task_id: int,
    ):
        """
        核心寫入和排程邏輯：將單一 Task 實例寫入 DB 並同步到 Scheduler。
        """
        task = (
            self.db.query(TaskORM)
            .options(joinedload(TaskORM.meeting))
            .filter(TaskORM.id == task_id)
            .first()
        )

        if not task:
            self.logger.error(f"Cannot schedule: Task ID {task_id} not found.")
            raise NotFoundError(detail=f"Task ID {task_id} not found.")

        meeting_name = task.meeting.meeting_name
        start_time = task.start_time
        end_time = task.end_time

        try:
            # 1. Start Job
            self.scheduler.add_job(
                start_recording,
                name=meeting_name,
                args=[task_id],
                trigger="date",
                run_date=start_time,
                id=f"task_start_{task_id}",
            )

            # 2. End Job
            self.scheduler.add_job(
                end_recording,
                name=meeting_name,
                args=[task_id],
                trigger="date",
                run_date=end_time,
                id=f"task_end_{task_id}",
            )
            self.logger.info(
                f"Scheduled Task {task_id} for meeting '{meeting_name}' "
                + f"from {start_time} to {end_time}."
            )

        except Exception as e:
            error_msg = f"Failed to schedule Task {task_id} for meeting '{meeting_name}'. Error: {e}"
            self.logger.error(error_msg)
            raise SchedulingError(detail=error_msg)

    def _calculate_execute_time(
        self,
        meeting: MeetingORM,
    ) -> List[tuple[datetime, datetime]]:
        """
        計算重複錄製任務的開始和結束時間。 \\
        保留中途更改重複錄製規則的可能性。 \\
        例：一會議需要重複錄製4次，錄製完前面兩次後，需要更改錄製時間等資訊。
        """
        if not meeting.repeat:
            return [(meeting.start_time, meeting.end_time)]

        all_times: list[tuple[datetime, datetime]] = []
        curr_start = meeting.start_time
        diff = meeting.end_time - meeting.start_time
        interval = timedelta(days=meeting.repeat_unit)
        now_time = datetime.now(TAIPEI_TZ)
        # self.logger.debug(f"{curr_start.tzinfo}, {meeting.repeat_end_date.tzinfo}")
        repeat_end_date = meeting.repeat_end_date
        while curr_start <= repeat_end_date:
            if curr_start >= now_time:
                all_times.append((curr_start, curr_start + diff))
            curr_start += interval

            if meeting.repeat_unit <= 0:
                break

        return all_times
