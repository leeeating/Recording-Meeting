from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Any, Optional, Self, List
from pydantic import BaseModel, Field, model_validator, field_validator, ConfigDict

from .enums import MeetingType, LayoutType, TaskStatus

TAIPEI_TZ = ZoneInfo("Asia/Taipei")


class CustomBaseModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        json_encoders={datetime: lambda v: v.astimezone(TAIPEI_TZ).isoformat()},
    )


# ----- Meeting Schemas -----
class MeetingCreateSchema(CustomBaseModel):
    """
    新的主輸入契約：用於創建 Meeting，並包含所有排程規則。
    """

    # 核心會議資訊 (不變)
    meeting_name: str = Field(..., max_length=100, description="會議名稱")
    meeting_type: MeetingType = Field(..., description="會議類型")
    meeting_url: Optional[str] = Field(None, max_length=200, description="會議連結")
    room_id: Optional[str] = Field(None, max_length=50, description="會議識別 ID")
    meeting_password: Optional[str] = Field(None, max_length=50, description="會議密碼")
    meeting_layout: LayoutType = Field(..., description="會議佈局")

    creator_name: str = Field(..., max_length=100, description="會議建立者名稱")
    creator_email: str = Field(..., max_length=100, description="會議建立者 Email")

    # 排程時間與規則 (從 Task 移入)
    start_time: datetime = Field(..., description="排程開始時間")
    end_time: datetime = Field(..., description="排程結束時間")
    repeat: bool = Field(False, description="是否重複排程")
    repeat_unit: Optional[int] = Field(None, description="重複的天數")
    repeat_end_date: Optional[datetime] = Field(None, description="重複結束日期")

    @field_validator("start_time", "end_time", "repeat_end_date", mode="before")
    @classmethod
    def set_datetime_timezone(cls, v: Any) -> datetime:
        # 使用相同的時區標準化邏輯 (已簡化)
        if isinstance(v, datetime):
            dt = v
        elif isinstance(v, str):
            dt = datetime.fromisoformat(v)
        else:
            raise TypeError("時間必須是 datetime 或 ISO 字串")

        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            return dt.replace(tzinfo=TAIPEI_TZ)
        else:
            return dt.astimezone(TAIPEI_TZ)

    @field_validator("repeat_unit", mode="before")
    @classmethod
    def coerce_int(cls, v: Any) -> Optional[int]:
        if v is None or v == "":
            return None

        try:
            return int(v)

        except (ValueError, TypeError):
            raise ValueError("重複天數必須是有效的數字格式")

    @field_validator("repeat_end_date", mode="after")
    @classmethod
    def force_to_end_of_day(cls, v: Optional[datetime]) -> Optional[datetime]:
        """
        將輸入的日期強制轉換為當日的 23:59:59
        """
        if v is None:
            return None

        return v.replace(hour=23, minute=59, second=59, microsecond=0)

    @model_validator(mode="after")
    def validate_meeting_rules(self) -> Self:
        has_url = bool(self.meeting_url)
        has_room_id = bool(self.room_id)
        has_password = bool(self.meeting_password)

        if not has_url and not (has_room_id and has_password):
            raise ValueError(
                "會議連線資訊不足。請提供 'meeting_url' 或 'room_id' 搭配 'password'。"
            )

        # 2. 檢查時間邏輯
        if self.start_time >= self.end_time:
            raise ValueError("排程結束時間必須嚴格晚於開始時間。")

        return self

    @model_validator(mode="after")
    def validate_repeat_rules(self) -> Self:
        if self.repeat:
            if self.repeat_unit is None or self.repeat_unit <= 0:
                raise ValueError("啟用重複排程時，'repeat_days' 必須為正整數。")
            if self.repeat_end_date is None:
                raise ValueError("啟用重複排程時，必須提供 'repeat_end_date'。")
            if self.repeat_end_date <= self.start_time:
                raise ValueError("'repeat_end_date' 必須晚於 'start_time'。")
        return self

    @model_validator(mode="after")
    def validate_start_end_time(self) -> Self:
        if datetime.now(TAIPEI_TZ) < self.start_time < self.end_time:
            return self

        raise ValueError("排程開始時間必須晚於當前時間。")


class MeetingResponseSchema(MeetingCreateSchema):

    id: int = Field(..., description="會議主鍵 ID")
    created_at: datetime = Field(..., description="會議創建時間")
    updated_at: datetime = Field(..., description="會議最後更新時間")
    # 這裡的 List 類型必須引用 TaskResponseSchema
    # tasks: List["TaskResponseSchema"] = Field(..., description="關聯的排程任務列表")


class MeetingQuerySchema(BaseModel):
    meeting_name_like: Optional[str] = Field(None, description="依據會議名稱模糊搜索。")
    start_time: Optional[datetime] = Field(None, description="過濾起始時間。")

    skip: int = Field(0, ge=0, description="跳過的記錄數。")
    limit: int = Field(100, le=200, description="每頁的記錄數。")

    sort_by: str = Field(
        "start_time", pattern=r"^(start_time|meeting_name)$", description="排序欄位。"
    )
    order: str = Field("asc", pattern=r"^(asc|desc)$", description="排序順序。")


# ----- Task Schemas -----
class TaskResponseSchema(CustomBaseModel):
    """
    用於返回 Task 資料的 Schema (只包含執行狀態和結果)。
    """

    id: int = Field(..., description="排程主鍵 ID")
    created_at: datetime = Field(..., description="排程創建時間")
    updated_at: datetime = Field(..., description="排程最後更新時間")

    status: TaskStatus = Field(..., description="排程狀態")
    save_path: Optional[str] = Field(
        None, max_length=200, description="錄製檔案儲存路徑"
    )

    # Meeting Info.
    meeting_name: str = Field(..., description="所屬會議名稱 (取自 Meeting)")
    start_time: datetime = Field(..., description="排程開始時間 (取自 Meeting)")
    end_time: datetime = Field(..., description="排程結束時間 (取自 Meeting)")
    creator_name: str = Field(..., description="會議建立者名稱 (取自 Meeting)")
    creator_email: str = Field(..., description="會議建立者 Email (取自 Meeting)")


class TaskQuerySchema(BaseModel):
    skip: int = Field(0, ge=0, description="跳過的記錄數。")
    limit: int = Field(100, le=200, description="每頁的記錄數。")

    sort_by: str = Field(
        "start_time", pattern=r"^(start_time|status)$", description="排序欄位。"
    )
    order: str = Field("asc", pattern=r"^(asc|desc)$", description="排序順序。")

    status: Optional[str] = Field(None, description="依據任務狀態過濾。")
    meeting_name_like: Optional[str] = Field(None, description="依據會議名稱模糊搜索。")
