from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Literal

class Config(BaseSettings):
    # Base Configuration
    PROJECT_NAME: str = Field(
        default="Meeting-Recorder",
        description="應用程式的名稱。"
    )

    # Database Configuration
    MEETING_DB_URL: str = Field(
        ..., 
        validation_alias="MEETING_DB_URL",
        description="會議資訊的資料庫連線字串。",
    )

    SCHEDULER_DB_URL: str = Field(
        ..., 
        validation_alias="SCHEDULER_DB_URL",
        description="錄製程式的資料庫連線字串。",
    )

    # logging Configuration
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="應用程式的日誌等級。",
    )

    # other Configuration
    MAX_RETRY_ATTEMPTS: int = Field(
        default=3,
        description="在錄製失敗時的最大重試次數。",
    )

    # 告訴 Pydantic 從 .env 檔案讀取設定
    model_config = SettingsConfigDict(env_file=".env")


config = Config()