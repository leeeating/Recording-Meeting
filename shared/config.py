import platform
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Literal

IS_WINDOWS: bool = platform.system() == "Windows"


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Base Configuration
    PROJECT_NAME: str = "Meeting-Recorder"

    # Database Configuration
    MEETING_DB_URL: str = Field(
        ...,
        validation_alias="MEETING_DB_URL",
        description="會議資訊的資料庫連線字串。",
    )

    SCHEDULER_DB_URL: str = Field(
        ...,
        validation_alias="SCHEDULER_DB_URL",
        description="排程器使用的資料庫連線字串。",
    )

    # logging Configuration
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="應用程式的日誌等級。",
    )

    # Path Configuration
    OBS_PATH: str = Field(
        default=(
            r"C:\Program Files\obs-studio\bin\64bit\obs64.exe"
            if IS_WINDOWS
            else "/Applications/OBS.app"
        ),
        description="OBS Studio 的安裝路徑。",
    )

    OBS_CWD: str = Field(
        default=(
            r"C:\Program Files\obs-studio\bin\64bit"
            if IS_WINDOWS
            else "/Applications/OBS.app/Contents/MacOS"
        ),
        description="OBS Studio 的工作目錄。",
    )

    ZOOM_APP_PATH: str = Field(
        default=r"C:\Users\linlab\AppData\Roaming\Zoom\bin\Zoom.exe",
        description="Zoom的安裝路徑"
    )

    WEBEX_APP_PATH: str = Field(
        default=r"C:\Users\linlab\AppData\Local\CiscoSparkLauncher\CiscoCollabHost.exe",
        description="Webex 的安裝路徑。",
    )

    # Webex UI Points
    WEBEX_GRID_POINT: str = Field(
        default="",
        description="網格按鈕的四邊",
    )

    WEBEX_STACKED_POINT: str = Field(
        default="",
        description="堆疊按鈕的四邊",
    )

    WEBEX_SIDE_BY_SIDE_POINT: str = Field(
        default="",
        description="側邊按鈕的四邊",
    )

    # Email Configuration
    EMAIL_USER: str = Field(
        ...,
        description="電子郵件帳號。",
    )

    EMAIL_APP_PASSWORD: str = Field(
        ...,
        description="電子郵件密碼。",
    )

    # Timeout Configuration
    MEETING_WAIT_TIMEOUT_IN_SECOND: int = Field(
        default=300,
        description="等待會議開始的超時時間（秒）。",
    )


config = Config()
