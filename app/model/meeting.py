from typing import List, TYPE_CHECKING
from sqlalchemy import Integer, String, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

from .enums import MeetingType, LayoutType

if TYPE_CHECKING:
    from .task import Task 


class Meeting(Base):
    """
    Columns:
    - id: 主鍵
    - meeting_name: 會議名稱
    - meeting_type: 會議類型 (Webex 或 Zoom)
    - meeting_url: 會議連結
    - room_id: 會議識別 ID
    - meeting_password: 會議密碼
    - meeting_layout: 會議佈局
    - tasks: 與 Task 的關聯，一個 Meeting 可以有多個 Task (邏輯上的關係)
    """
    __tablename__ = "meetings" 

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Base Meeting Info.
    meeting_name: Mapped[str] = mapped_column(
    String(100), nullable=False, doc="會議名稱"
    )

    meeting_type: Mapped[MeetingType] = mapped_column(
        Enum(MeetingType), nullable=False, doc="會議類型"
    )

    # Entry Meeting Info.
    meeting_url: Mapped[str] = mapped_column(
        String(200), nullable=True, doc="會議連結"
    )

    room_id: Mapped[str] = mapped_column(
        String(50), nullable=True, doc="會議識別 ID"
    )
    
    meeting_password: Mapped[str | None] = mapped_column(
        String(50), nullable=True, doc="會議密碼"
    )

    # Layout Info.
    meeting_layout: Mapped[LayoutType] = mapped_column(
        Enum(LayoutType), doc="會議佈局"
    )
    
    # 關係：一個 Meeting 可以有多個 Task (邏輯上的關係)
    tasks: Mapped[List["Task"]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan", # 刪除會議時，刪除其所有排程
    )