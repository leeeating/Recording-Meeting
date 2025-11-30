from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Boolean, DateTime, Numeric, Enum, ForeignKey
from app.core.database import Base

from .enums import TaskStatus

if TYPE_CHECKING:
    from .meeting import Meeting 

class Task(Base):
    """
    Columns:
    - id: 主鍵
    - user_name: 使用者名稱
    - user_email: 使用者 Email
    - start_time: 開始時間
    - end_time: 結束時間
    - repeat: 是否重複排程
    - repeat_days: 重複的天數
    - repeat_end_date: 重複結束日期
    - status: 排程狀態
    - save_path: 錄製檔案儲存路徑
    - meeting: 與 Meeting 的關聯，一個排程只能對應一個會議 (邏輯上的關係)
    """

    __tablename__ = "tasks"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    user_name: Mapped[str] = mapped_column(
        String(100), nullable=False, doc="使用者名稱"
    )
    
    user_email: Mapped[str] = mapped_column(
        String(100), nullable=False, doc="使用者 Email"
    )
    
    start_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, doc="開始時間"
    )

    end_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, doc="結束時間"
    )

    repeat: Mapped[Boolean] = mapped_column(
        Boolean, nullable=False, doc="是否重複排程",
        default=False
    )

    repeat_days: Mapped[int | None] = mapped_column(
        Numeric, nullable=True, doc="重複的天數"
    )

    repeat_end_date: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, doc="重複結束日期"
    )

    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus), nullable=False, doc="排程狀態",
        default=TaskStatus.UPCOMING
    )

    save_path: Mapped[str] = mapped_column(
        String(200), nullable=True, doc="錄製檔案儲存路徑"
    )

    meeting: Mapped["Meeting"] = relationship(
        back_populates="tasks",
    )

    meeting_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("meetings.id"), nullable=False, index=True, doc="對應 Meeting 表的主鍵"
    )