import logging
import time
import webbrowser
from urllib.parse import parse_qs, urlparse

# from pywinauto import Desktop

from shared.config import config

from .utils import action

logger = logging.getLogger(__name__)


class ZoomManager:
    WAIT_TIMEOUT = config.MEETING_WAIT_TIMEOUT_IN_SECOND
    WAIT_TIMEOUT = 30

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
        """
        if self.meeting_url is None and (
            self.password is None or self.meeting_id is None
        ):
            logger.error("必須提供 meeting_url 或 meeting_id 和 password")
            raise ValueError("必須提供 meeting_url 或 meeting_id 和 password")

        logger.debug(f"Starting Zoom meeting {self.meeting_name} ")
        zoom_meeting_url = self._parse_meeting_url()

        with action("ZOOM開啟URL Schemas", logger):
            webbrowser.open(zoom_meeting_url)

        time.sleep(2)

        with action("[連線中]等待連線中", logger):
            connect_window = Desktop(backend="uia").window(title_re=".*連線中.*")
            # connect_window.set_focus()
            connect_window.wait_not(
                "exists",
                timeout=self.WAIT_TIMEOUT,
                retry_interval=1,
            )

        with action("[Zoom Workplace]等待主持人允許", logger):
            main_window = Desktop(backend="uia").window(
                title="Zoom Workplace",
                class_name="zWaitingRoomWndClass",
            )
            main_window.wait_not(
                "exists",
                timeout=self.WAIT_TIMEOUT,
                retry_interval=1,
            )

        time.sleep(3)

        self._change_layout_by_desktop()

    def _change_layout_by_desktop(self):
        """
        Use UI Automation to change Zoom layout. \\
        Don't need point of each layout button.
        我嘗試下來，這步驟的成功與否應該會依賴OBS開啟時是否有安全模式的提示框
        """

        with action("[Zoom會議]Zoom視窗最大化", logger):
            meeting_window = Desktop(backend="uia").window(title_re=".*Zoom 會議.*")
            meeting_window.maximize()
            meeting_window.set_focus()

        with action("[Zoom會議]按下檢視按鈕", logger):
            # detect layout button
            meeting_window = Desktop(backend="uia").window(title_re=".*Zoom 會議.*")
            btn = meeting_window.child_window(
                title="檢視",
                control_type="Button",
            )
            btn.click_input()

        # time.sleep(1)

        with action("[Zoom會議]選擇排版", logger):
            layout_btn = meeting_window.child_window(
                title_re=f".*{self.layout}.*",
                control_type="MenuItem",
                found_index=0,
            )
            layout_btn.click_input()

        logger.info(f"Successfully changed layout to {self.layout}.")

    # TODO:
    def _change_layout_by_autogui(self):
        pass

    def _parse_meeting_url(self) -> str:
        """
        Zoom can use url schema to entry meeting. \\
        URL example: zoommtg://zoom.us/join?confno=123456789&pwd=xxxx
        """
        meeting_id = self.meeting_id
        password = self.password

        if self.meeting_url:
            parsed_url = urlparse(self.meeting_url)
            query_params = parse_qs(parsed_url.query)
            meeting_id = parsed_url.path.split("/")[-1]
            password = query_params.get("pwd", [None])[0]

        return f"zoommtg://zoom.us/join?confno={meeting_id}&pwd={password}"
