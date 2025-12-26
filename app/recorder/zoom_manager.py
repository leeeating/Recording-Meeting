import logging
import webbrowser
from urllib.parse import parse_qs, urlparse

from pywinauto import Desktop

# from shared.config import config
from .utils import action

logger = logging.getLogger(__name__)


class ZoomManager:
    WAIT_TIMEOUT = 30  # seconds

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

        :param meeting_name: meeting name for logging
        :type meeting_name: str
        :param meeting_url: original meeting url
        :type meeting_url: str | None
        :param meeting_id: meeting ID
        :type meeting_id: str | None
        :param password: meeting password
        :type password: str | None
        :return: success status
        :rtype: bool
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

        with action("[連線中]等待連線中", logger):
            connect_window = Desktop(backend="uia").window(title_re=".*連線中.*")
            connect_window.set_focus()
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

        self._change_layout_by_uia()

    def _change_layout_by_uia(self):
        """
        Use UI Automation to change Zoom layout. \\
        Don't support MacOS. \\
        Don't need point of each layout button.
        """

        with action("[Zoom會議]Zoom視窗最大化", logger):
            meeting_window = Desktop(backend="uia").window(title_re=".*Zoom 會議.*")
            meeting_window.maximize()
            meeting_window.set_focus()

        with action("[Zoom會議]按下檢視按鈕", logger):
            # detect layout button
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


if __name__ == "__main__":
    zoom_manager = ZoomManager(
        meeting_name="Test",
        meeting_url="https://us05web.zoom.us/j/8631054479?pwd=XGui4JAL9Kx6bH8DMFUo9IPOG12YlS.1",
        layout="演講者",
    )
    zoom_manager.join_meeting_and_change_layout()
