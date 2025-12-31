import sys
import logging
import re
import subprocess
import time
import webbrowser

import pyautogui
if sys.platform == "win32":
    from pywinauto import Desktop

from shared.config import config

from .utils import action, copy_paste

logger = logging.getLogger(__name__)


class WebexManager:
    WAIT_TIMEOUT = 30  # seconds

    def __init__(
        self,
        meeting_name: str,
        meeting_url: str = "",
        meeting_id: str = "",
        password: str = "",
        layout: str = "grid",
    ):
        self.meeting_url = meeting_url
        self.meeting_name = meeting_name
        self.meeting_id = meeting_id
        self.password = password
        self.layout = layout

        logger.info(f"WebexManager initialized for: {self.meeting_name}")

    def join_meeting_and_change_layout(self):
        """
        執行整個加入會議的自動化流程
        """
        # 基礎驗證
        if self.meeting_url is None and (
            self.password is None or self.meeting_id is None
        ):
            logger.error("必須提供 meeting_url 或 (meeting_id + password)")
            raise ValueError("必須提供 meeting_url 或 (meeting_id + password)")

        logger.info(f"開始執行自動化加入流程：{self.meeting_name}")

        self._launch_webex()
        self._input_meeting_info()

        self._handle_waiting_room_and_change_layout()

    def _launch_webex(self):
        """
        Open webex app and typing meeting information
        """
        with action("啟動Webex應用程式", logger):
            subprocess.Popen([config.WEBEX_APP_PATH])

        time.sleep(5)

        with action("按下[加入會議]按鈕，進入輸入頁面", logger):
            main_window = Desktop(backend="uia").window(
                title="Webex", class_name="MainWindow"
            )
            main_window.child_window(
                title_re=" .*加入會議.*",
                control_type="Button",
            ).click_input()

    def _launch_by_url(self):
        """
        使用內部 self.meeting_url 進入
        deprecated
        """
        with action("開啟Webex URL", logger):
            webbrowser.open(self.meeting_url)

        time.sleep(5)

        with action("按下[加入會議]按鈕", logger):
            waiting_window = Desktop(backend="uia").window(title_re=".*準備加入.*")
            waiting_window.set_focus()
            waiting_window.child_window(
                title_re=".*加入.*",
                control_type="Button",
            ).click_input()

    def _input_meeting_info(self):
        if self.meeting_url:
            with action("輸入URL", logger):
                copy_paste(self.meeting_url)

        else:
            with action("輸入ID/PW", logger):
                copy_paste(self.meeting_id)
                copy_paste(self.password)

        time.sleep(1)

        with action("按下[加入會議]按鈕", logger):
            waiting_window = Desktop(backend="uia").window(title_re=".*準備加入.*")
            waiting_window.set_focus()
            btn = waiting_window.child_window(
                title_re=".*加入.*",
                control_type="Button",
            )
            btn.wait("ready", timeout=60)
            btn.click_input()

    def _handle_waiting_room_and_change_layout(self):
        """
        處理進入會議後的版面切換
        Webex中多數元件有相同屬性，難以直接辨認，使用直接點擊指定座標。
        """
        # time.sleep(5)
        with action("點擊[版面配置]按鈕", logger):
            meeting_window = Desktop(backend="uia").window(
                title_re=".*(meeting|Personal Room).*"
            )
            meeting_window.set_focus()
            meeting_window.maximize()
            btn = meeting_window.child_window(
                title_re="版面配置",
                auto_id="ScannedByVDI",
                control_type="Button",
                found_index=0,
            )
            try:
                btn.wait("ready", timeout=self.WAIT_TIMEOUT)
                btn.click_input()

            except Exception as e:
                raise TimeoutError(f"未出現[版面配置]，因為等待主持人允許超時, {e}")

        with action(f"點擊{self.layout.upper()}", logger):
            attr_name = f"WEBEX_{self.layout.upper()}_POINT"
            point_str = getattr(config, attr_name, None)
            if point_str:
                x, y = self._parse_button_point(point_str)
                pyautogui.click(x, y)
            else:
                e = "Layout point is None, please check point setting"
                logger.warning(e)
                raise ValueError(e)

        with action("靜音", logger):
            btn = meeting_window.child_window(
                title_re=".*靜音.*",
                control_type="Button",
                found_index=0,
            )
            btn.wait("ready", timeout=60)
            btn.click_input()

    def _parse_button_point(self, point_str: str) -> tuple[int, int]:
        """
        通用的座標解析工具
        point schema: '[l=1696,t=97,r=1787,b=177]'
        代表按鈕元件的上下左右座標
        """
        nums = re.findall(r"\d+", point_str)
        if len(nums) == 4:
            left, top, right, bottom = map(int, nums)
            return ((left + right) // 2, (top + bottom) // 2)
        return (0, 0)
