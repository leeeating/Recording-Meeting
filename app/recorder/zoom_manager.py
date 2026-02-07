import logging
import sys
import time
import webbrowser
from urllib.parse import parse_qs, urlparse

from shared.config import WAIT_TIMEOUT

if sys.platform == "win32":
    from pywinauto import Desktop

from .utils import action, maximize_window

logger = logging.getLogger(__name__)


class ZoomManager:
    def __init__(
        self,
        meeting_name: str,
        meeting_url: str = "",
        meeting_id: str = "",
        password: str = "",
        layout: str = "grid",
    ):
        self.meeting_name = meeting_name
        self.meeting_url = meeting_url
        self.meeting_id = meeting_id
        self.password = password
        self.layout = layout

        logger.info(f"ZoomManager initialized for: {self.meeting_name}")

    def join_meeting_and_change_layout(self):
        """
        Use URL schema to join Zoom meeting. \\
        And handle waiting room if exists. \\
        Wait up to **WAIT_TIMEOUT** seconds. It can setting in env file.

        Detail Action:
            ZOOM開啟URL Schemas - Critical Action
            [連線中]等待連線中 - Critical Action
            [Zoom Workplace]等待主持人允許 - Critical Action
            [Zoom會議]按下檢視按鈕 - Error Action
            [Zoom會議]選擇排版 - Error Action
        """
        if self.meeting_url is None and (
            self.password is None or self.meeting_id is None
        ):
            logger.error("必須提供 meeting_url 或 meeting_id 和 password")
            raise ValueError("必須提供 meeting_url 或 meeting_id 和 password")

        logger.debug(f"Starting Zoom meeting {self.meeting_name} ")
        zoom_meeting_url = self._parse_meeting_url()

        with action("ZOOM開啟URL Schemas", logger, is_critical=True):
            webbrowser.open(zoom_meeting_url)

        time.sleep(2)

        ## 在執行[等待連線中]、[等待主持人允許] 會因為執行權限的問題，出現偵測視窗失敗
        ## 偵測失敗後，會導致Timeout檢查一起失敗，但不會跳出錯誤提醒
        ## 目前使用[管理員權限]執行可以解決，但無法確保其他bug出現
        with action("[連線中]等待連線中", logger, is_critical=True):
            connect_window = Desktop(backend="uia").window(title_re=".*連線中.*")
            logger.debug(connect_window.exists())
            connect_window.wait_not(
                "exists",
                timeout=WAIT_TIMEOUT,
                retry_interval=1,
            )

        logger.debug("Before sleep")
        time.sleep(5)
        logger.debug("after sleep")

        with action("[Zoom Workplace]等待主持人允許", logger, is_critical=True):
            main_window = Desktop(backend="uia").window(
                title="Zoom Workplace",
                class_name="zWaitingRoomWndClass",
            )
            logger.info(f"Zoom Workplace is exists: {main_window.exists()}")
            print(f"Zoom Workplace is exists: {main_window.exists()}")
            main_window.wait_not(
                "exists",
                timeout=WAIT_TIMEOUT,
            )

        time.sleep(3)

        self._change_layout_by_desktop()

    def _change_layout_by_desktop(self):
        """
        Use UI Automation to change Zoom layout. \\
        Don't need point of each layout button.
        我嘗試下來，這步驟的成功與否應該會依賴OBS開啟時是否有安全模式的提示框
        """
        meeting_window = Desktop(backend="uia").window(title_re=".*Zoom 會議.*")
        logger.info(f"[Zoom 會議] is exists: {meeting_window.exists()}")

        with action("[Zoom會議]Zoom視窗最大化", logger):
            maximize_window(meeting_window)

        with action("[Zoom會議]按下檢視按鈕", logger):
            meeting_window.wait("ready", timeout=10)

            btn = meeting_window.child_window(title="檢視", control_type="Button")

            if btn.exists(timeout=5):
                btn.wait("visible", timeout=3)
                try:
                    btn.iface_invoke.Invoke()  # 邏輯點擊
                except Exception:
                    btn.click_input()  # 如果邏輯點擊失敗，再用物理點擊

        time.sleep(0.5)

        with action("[Zoom會議]選擇排版", logger):
            layout_btn = meeting_window.child_window(
                title_re=f".*{self.layout}.*",
                control_type="MenuItem",
                found_index=0,
            )
            layout_btn.click_input()
            # Implement window maximization here will succeed
            meeting_window.maximize()

            logger.info(f"Successfully changed layout to {self.layout}.")

    # TODO:
    def _change_layout_by_autogui(self):
        pass

    def _parse_meeting_url(self) -> str:
        """
        Zoom can use url schema to entry meeting. \\
        URL example: zoommtg://zoom.us/join?confno=123456789&pwd=xxxx
        """
        meeting_id = self.meeting_id.replace(" ", "")
        password = self.password.replace(" ", "")
        if self.meeting_id and self.password:
            return f"zoommtg://zoom.us/join?confno={meeting_id}&pwd={password}"

        parsed_url = urlparse(self.meeting_url)
        query_params = parse_qs(parsed_url.query)
        meeting_id = parsed_url.path.split("/")[-1]
        password = query_params.get("pwd", [None])[0]
        logger.debug(f"zoommtg://zoom.us/join?confno={meeting_id}&pwd={password}")
        return f"zoommtg://zoom.us/join?confno={meeting_id}&pwd={password}"
