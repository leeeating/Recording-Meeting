from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

from .enums import LayoutType, MeetingType

if TYPE_CHECKING:
    from .task import TaskORM


class MeetingORM(Base):
    """
    Columns: (會議的定義與排程規則)
    - id: 主鍵
    - meeting_name: 會議名稱
    - meeting_type: 會議類型
    - meeting_layout: 會議佈局
    - creator_name/email: 會議建立者
    - start_time/end_time: 會議時間定義
    - repeat : 是否重複排程

    nullable:
    - meeting_url: 會議連結
    - room_id: 會議識別 ID
    - meeting_password: 會議密碼
    - repeat_unit/repeat_end_date: 會議重複規則
    - tasks: 與 Task 的關聯 (One-to-Many)
    """

    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    meeting_name: Mapped[str] = mapped_column(
        String(100), nullable=False, doc="會議名稱"
    )

    meeting_type: Mapped[MeetingType] = mapped_column(
        Enum(MeetingType), nullable=False, doc="會議類型"
    )

    meeting_url: Mapped[str] = mapped_column(String(200), nullable=True, doc="會議連結")

    room_id: Mapped[str] = mapped_column(String(50), nullable=True, doc="會議識別 ID")

    meeting_password: Mapped[str | None] = mapped_column(
        String(50), nullable=True, doc="會議密碼"
    )

    meeting_layout: Mapped[LayoutType] = mapped_column(
        Enum(LayoutType), nullable=True, doc="會議佈局"
    )

    creator_name: Mapped[str] = mapped_column(
        String(100), nullable=False, doc="會議建立者名稱"
    )
    creator_email: Mapped[str] = mapped_column(
        String(100), nullable=False, doc="會議建立者 Email"
    )

    start_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, doc="排程開始時間"
    )

    end_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, doc="排程結束時間"
    )

    repeat: Mapped[Boolean] = mapped_column(
        Boolean, nullable=False, doc="是否重複排程", default=False
    )

    repeat_unit: Mapped[int] = mapped_column(
        Integer, nullable=True, doc="重複的週期(天)"
    )

    repeat_end_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=True, doc="重複結束日期"
    )

    tasks: Mapped[List["TaskORM"]] = relationship(
        back_populates="meeting",
        cascade="all, delete-orphan",
    )
