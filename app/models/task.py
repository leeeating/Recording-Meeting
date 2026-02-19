from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TZDateTime

from .enums import TaskStatus

if TYPE_CHECKING:
    from .meeting import MeetingORM


class TaskORM(Base):
    """
    Columns: (單一排程的執行與狀態)
    - id: 主鍵
    - status: 排程狀態
    - start_time/end_time: 排程時間定義
    - duration_minutes: 任務持續時間（分鐘）
    - save_path: 錄製檔案儲存路徑
    - meeting_id: 
    """

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus), nullable=False, doc="排程狀態", default=TaskStatus.UPCOMING
    )

    start_time: Mapped[datetime] = mapped_column(TZDateTime, nullable=False, doc="任務開始時間")

    end_time: Mapped[datetime] = mapped_column(TZDateTime, nullable=False, doc="任務結束時間")

    duration_minutes: Mapped[int] = mapped_column(
        Integer, nullable=True, doc="任務持續時間（分鐘）"
    )

    save_path: Mapped[str | None] = mapped_column(
        String(200), nullable=True, doc="錄製檔案儲存路徑"
    )

    meeting: Mapped["MeetingORM"] = relationship(
        back_populates="tasks",
    )

    meeting_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("meetings.id"),
        nullable=False,
        index=True,
        doc="對應 Meeting 表的主鍵",
    )

    @property
    def meeting_name(self) -> str:
        return self.meeting.meeting_name if self.meeting else ""

    @property
    def creator_name(self) -> str:
        return self.meeting.creator_name if self.meeting else ""

    @property
    def creator_email(self) -> str:
        return self.meeting.creator_email if self.meeting else ""
