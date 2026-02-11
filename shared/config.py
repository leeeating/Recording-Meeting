import logging
import os
import platform
from typing import Callable, Literal
from zoneinfo import ZoneInfo

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer

IS_WINDOWS: bool = platform.system() == "Windows"


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Base Configuration
    PROJECT_NAME: str = "Meeting-Recorder"

    # envronment
    ENV: Literal["prod", "dev"] = Field(
        default="dev", description="環境設定，先以測試跟生產為主，日後可依需求增加"
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
        description="Zoom的安裝路徑",
    )

    ZOOM_SCENE_NAME: str = Field(
        ...,
        description="OBS中為ZOOM設定的場景名稱，最好先設定好所有參數",
    )

    WEBEX_APP_PATH: str = Field(
        default=r"C:\Users\linlab\AppData\Local\CiscoSparkLauncher\CiscoCollabHost.exe",
        description="Webex 的安裝路徑。",
    )

    WEBEX_SCENE_NAME: str = Field(
        ...,
        description="OBS中為ZOOM設定的場景名稱，最好先設定好所有參數",
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
    DEFAULT_USER_EMAIL: str = Field(
        ...,
        description="電子郵件帳號。",
    )

    EMAIL_APP_PASSWORD: str = Field(
        ...,
        description="電子郵件密碼。",
    )

    ADDRESSEES_EMAIL: str = Field(
        ...,
        description="收件者信箱"
    )

    # Timeout Configuration
    MEETING_WAIT_TIMEOUT_IN_SECOND: int = Field(
        default=300,
        description="等待會議開始的超時時間（秒）。",
    )

    # test configurtion
    RECORDING_DURATION_IN_MINUTE: int = Field(
        default=1, description="測試時的錄影設定時間"
    )


config = Config()

TAIPEI_TZ = ZoneInfo("Asia/Taipei")

# --- Hot Reload Infrastructure ---

_reload_callbacks: list[Callable[[set[str]], None]] = []
_logger = logging.getLogger(__name__)

# 需要重啟才能生效的欄位
_RESTART_REQUIRED_FIELDS = {"MEETING_DB_URL", "SCHEDULER_DB_URL"}


def register_reload_callback(callback: Callable[[set[str]], None]):
    """註冊 config reload 後的回呼函式，會收到變更欄位名稱的 set。"""
    _reload_callbacks.append(callback)


def reload_config() -> set[str]:
    """重新讀取 .env，in-place 更新 config 物件。回傳有變更的欄位名稱。"""
    new_config = Config()
    changed: set[str] = set()

    for field_name in Config.model_fields:
        old_val = getattr(config, field_name)
        new_val = getattr(new_config, field_name)
        if old_val != new_val:
            changed.add(field_name)
            if field_name in _RESTART_REQUIRED_FIELDS:
                _logger.warning(f"'{field_name}' 已變更，但需要重啟才能生效")
            else:
                object.__setattr__(config, field_name, new_val)
                _logger.info(f"Config '{field_name}' 已重新載入")

    for cb in _reload_callbacks:
        try:
            cb(changed)
        except Exception as e:
            _logger.error(f"Reload callback 失敗: {e}")

    return changed


def save_env(updates: dict[str, str], env_path: str = ".env"):
    """讀取現有 .env，更新指定欄位，寫回檔案。"""
    lines: list[str] = []
    existing_keys: set[str] = set()

    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

    new_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if "=" in stripped and not stripped.startswith("#"):
            key = stripped.split("=", 1)[0].strip()
            if key in updates:
                new_lines.append(f"{key}={updates[key]}\n")
                existing_keys.add(key)
                continue
        new_lines.append(line)

    # 新增不存在的 key
    for key, val in updates.items():
        if key not in existing_keys:
            new_lines.append(f"{key}={val}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)


class _EnvFileHandler(FileSystemEventHandler):
    """Watchdog 檔案事件處理器"""

    def __init__(self, env_path: str = ".env"):
        super().__init__()
        self._env_path = env_path
        self._env_filename = os.path.basename(env_path)

    def on_modified(self, event: FileSystemEvent):
        """檔案被修改時觸發"""
        if event.is_directory:
            return

        # 只處理 .env 檔案
        if os.path.basename(event.src_path) == self._env_filename:
            _logger.info(".env 檔案變更，重新載入設定...")
            changed = reload_config()
            if changed:
                _logger.info(f"已更新欄位: {changed}")


class ConfigWatcher:
    """使用 Watchdog 即時監聽 .env 檔案變更"""

    def __init__(self, env_path: str = ".env"):
        self._env_path = env_path
        self._env_dir = os.path.dirname(env_path) or "."
        self._observer: Observer | None = None
        self._handler: _EnvFileHandler = _EnvFileHandler(env_path)

    def start(self):
        """啟動檔案監聽"""
        if self._observer is not None and self._observer.is_alive():
            return

        self._observer = Observer()
        self._observer.schedule(self._handler, self._env_dir, recursive=False)
        self._observer.start()
        _logger.info("ConfigWatcher 已啟動（使用 Watchdog）")

    def stop(self):
        """停止檔案監聽"""
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=5)
            _logger.info("ConfigWatcher 已停止")
