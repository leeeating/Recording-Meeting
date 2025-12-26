import logging
import re
import subprocess
import time
import webbrowser

import pyautogui
import pyperclip
from pywinauto import Desktop

# 假設你的環境已有此設定
from shared.config import config
from .utils import action

logger = logging.getLogger(__name__)


class WebexManager:
    WAIT_TIMEOUT = 120  # seconds

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
            logger.error("錯誤：必須提供 meeting_url 或 (meeting_id + password)")
            return False

        logger.info(f"開始執行自動化加入流程：{self.meeting_name}")

        if self.meeting_url:
            self._enter_by_url()
        else:
            self._enter_by_id_pw()

        self._handle_waiting_room_and_change_layout()

    def _enter_by_url(self):
        """使用內部 self.meeting_url 進入"""
        with action("開啟Webex URL", logger):
            webbrowser.open(self.meeting_url)

        time.sleep(2)

        with action("按下[加入會議]按鈕", logger):
            waiting_window = Desktop(backend="uia").window(title_re=".*準備加入.*")
            waiting_window.set_focus()
            waiting_window.child_window(
                title_re=".*加入.*",
                control_type="Button",
            ).click_input()

    # TODO:
    def _enter_by_id_pw(self):
        """使用內部 self.meeting_id/password 進入"""
        with action("啟動Webex應用程式", logger):
            subprocess.Popen([config.WEBEX_APP_PATH])

        time.sleep(2)

        with action("按下[加入會議]按鈕，進入輸入頁面", logger):
            main_window = Desktop(backend="uia").window(
                title="Webex", class_name="MainWindow"
            )
            main_window.child_window(
                title_re=" .*加入會議.*",
                control_type="Button",
            ).click_input()

        time.sleep(2)

        with action("輸入ID/PW", logger):
            # 填入 ID
            pyperclip.copy(self.meeting_id)
            pyautogui.hotkey("ctrl", "v")
            pyautogui.press("enter")
            time.sleep(1)

            if self.password:
                pyperclip.copy(self.password)
                pyautogui.hotkey("ctrl", "v")
                pyautogui.press("enter")

        time.sleep(2)

        with action("按下[加入會議]按鈕", logger):
            waiting_window = Desktop(backend="uia").window(title_re=".*準備加入.*")
            waiting_window.set_focus()
            waiting_window.child_window(
                title_re=".*加入.*",
                control_type="Button",
            ).click_input()

    def _handle_waiting_room_and_change_layout(self):
        """
        處理進入會議後的版面切換
        Webex中多數元件有相同屬性，難以直接辨認，使用直接點擊指定座標。
        """
        with action("點擊[版面配置]按鈕", logger):
            meeting_window = Desktop(backend="uia").window(title_re=".*meeting.*")
            meeting_window.set_focus()
            meeting_window.maximize()
            btn = meeting_window.child_window(
                title_re="版面配置",
                auto_id="ScannedByVDI",
                control_type="Button",
                found_index=0,
            )
            btn.click_input()

        with action("點擊指定版面", logger):
            attr_name = f"WEBEX_{self.layout.upper()}_POINT"
            point_str = getattr(config, attr_name, None)
            if point_str:
                x, y = self._parse_button_point(point_str)
                pyautogui.click(x, y)

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


if __name__ == "__main__":
    webex = WebexManager(
        meeting_url="https://meet1403.webex.com/...",
        meeting_name="我的測試會議",
        layout="side_by_side",
    )

    webex.join_meeting_and_change_layout()
