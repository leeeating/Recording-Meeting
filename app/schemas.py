from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Any, Optional, Self, List
from pydantic import (
    BaseModel, 
    Field, 
    model_validator, 
    field_validator, 
    ConfigDict, 
    ValidationInfo
)

from .models.enums import MeetingType, LayoutType, TaskStatus 


class CustomBaseModel(BaseModel):
    """
    自定義基類：統一定義所有 Schemas 的 ORM 轉換、嚴格模式和 JSON 輸出格式。
    """
    model_config = ConfigDict(
        from_attributes=True,
        # 嚴格限制：禁止傳入 Schema 中未定義的額外欄位 (Fail Fast 原則)
        extra='forbid',
        json_encoders={datetime: lambda v: v.isoformat()}
    )


class MeetingCreateSchema(CustomBaseModel):
    """
    用於創建 Meeting 的 Schema。
    """
    meeting_name: str = Field(
        ..., max_length=100, description="會議名稱"
    )
    
    meeting_type: MeetingType = Field(
        ..., description="會議類型"
    )

    meeting_url: Optional[str] = Field(
        None, max_length=200, description="會議連結"
    )
    
    room_id: Optional[str] = Field(
        None, max_length=50, description="會議識別 ID"
    )

    meeting_password: Optional[str] = Field(
        None, max_length=50, description="會議密碼"
    )
    
    meeting_layout: LayoutType = Field(
        ..., description="會議佈局"
    )

    @model_validator(mode='before')
    @classmethod
    def validate_meeting_entry(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
            
        url = data.get('meeting_url')
        room_id = data.get('room_id')
        
        has_url = bool(url)
        has_room_id = bool(room_id)

        if not has_url and not has_room_id:
            raise ValueError("會議連線資訊不足。請提供 'meeting_url' 或 'room_id'。")
            
        return data

class MeetingResponseSchema(MeetingCreateSchema):
    """
    用於返回 Meeting 資料的 Schema。
    """
    id: int = Field(..., description="會議主鍵 ID")
    created_at: datetime = Field(..., description="會議創建時間")
    updated_at: datetime = Field(..., description="會議最後更新時間")
    tasks: List['TaskResponseSchema'] = Field(..., description="關聯的排程任務列表")


class TaskCreateSchema(CustomBaseModel):
    """
    用於創建 Task 的 Schema。
    """
    user_name: str = Field(
        ..., max_length=100, description="使用者名稱"
    )
    
    user_email: str = Field(
        ..., max_length=100, description="使用者 Email"
    )

    start_time: datetime = Field(
        ..., description="開始時間"
    )

    end_time: datetime = Field(
        ..., description="結束時間"
    )

    repeat: bool = Field(
        False, description="是否重複排程"
    )

    repeat_days: Optional[int] = Field(
        None, description="重複的天數"
    )

    repeat_end_date: Optional[datetime] = Field(
        None, description="重複結束日期"
    )

    status: TaskStatus = Field(
        TaskStatus.UPCOMING, description="排程狀態"
    )

    save_path: Optional[str] = Field(
        None, max_length=200, description="錄製檔案儲存路徑"
    )

    @field_validator('start_time', 'end_time', mode='before')
    @classmethod
    def set_datetime_timezone(cls, v: Any, info: ValidationInfo) -> datetime:
        """
        將輸入的日期時間標準化為帶有 Asia/Taipei 時區的 datetime 物件。
        """
        # 可以使用 info.field_name 來確定當前驗證的是哪個欄位 (如果需要差異化處理的話)
        field_name = info.field_name 
        
        if isinstance(v, str):
            try:
                dt = datetime.fromisoformat(v)
            except ValueError:
                 raise ValueError(f"{field_name} 字串格式錯誤，請使用 ISO 8601 格式。")
                
        elif isinstance(v, datetime):
            dt = v

        else:
            raise TypeError(f"{field_name} 必須是 datetime 物件或 ISO 格式字串，接收到 {type(v)}")

        TAIPEI_TZ = ZoneInfo("Asia/Taipei")

        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            return dt.replace(tzinfo=TAIPEI_TZ)
        else:
            return dt.astimezone(TAIPEI_TZ)


    @model_validator(mode='after')
    def time_validator(self) -> Self: 
        if self.start_time >= self.end_time:
            raise ValueError("排程結束時間必須嚴格晚於開始時間。")
        return self


class TaskResponseSchema(TaskCreateSchema):
    """
    用於返回 Task 資料的 Schema。
    """
    id: int = Field(..., description="排程主鍵 ID")
    status: TaskStatus = Field(..., description="排程狀態")
    save_path: Optional[str] = Field(..., description="錄製檔案儲存路徑")
    created_at: datetime = Field(..., description="排程創建時間")
    updated_at: datetime = Field(..., description="排程最後更新時間")
    meeting_id: int = Field(..., description="對應 Meeting 表的主鍵")