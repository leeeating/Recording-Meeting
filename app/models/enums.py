from enum import Enum
from typing import final


@final
class MeetingType(str, Enum):
    WEBEX = "Webex"
    ZOOM = "Zoom"


@final
class LayoutType(str, Enum):
    # webex
    GRID = "網格"
    STACKED = "堆疊"
    SIDE_BY_SIDE = "並排"
    # zoom
    SPEAKER = "演講者"
    GALLERY = "圖庫"
    MULTIPLE_SPEAKERS = "多位演講者"
    FOCUS = "沉浸式"


@final
class TaskStatus(str, Enum):
    UPCOMING = "upcoming"
    RECORDING = "recording"
    COMPLETED = "completed"
    FAILED = "failed"
