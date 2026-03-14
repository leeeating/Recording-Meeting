import logging
import re
import subprocess
import sys
import time
import webbrowser

import pyautogui
from typing_extensions import deprecated

if sys.platform == "win32":
    import win32con
    import win32gui
    from pywinauto import Desktop

from shared.config import config

from .utils import action, copy_paste, find_window_hwnd, set_foreground

logger = logging.getLogger(__name__)


class WebexManager:
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
        self.setting = {
            "meeting_name": meeting_name,
            "meeting_type": "WEBEX",
            "logger": logger,
        }

    def join_meeting_and_change_layout(self):
        """
        執行整個加入會議的自動化流程

        Detial Action :
            啟動Webex應用程式 - Critical Action
            按下[加入會議]按鈕，進入輸入頁面 - Critical Action
            輸入URL - Critical Action
            輸入ID/PW - Critical Action
            按下[加入會議]按鈕 - Critical Action
            點擊[版面配置]按鈕 - Critical Action
            選擇排版 - Error Action
            靜音 - Error Action
        """
        # 基礎驗證
        if self.meeting_url is None and (
            self.password is None or self.meeting_id is None
        ):
            logger.error("必須提供 meeting_url 或 (meeting_id + password)")
            raise ValueError("必須提供 meeting_url 或 (meeting_id + password)")

        self._launch_webex()
        self._input_meeting_info()
        self._handle_waiting_room_and_change_layout()

    def _launch_webex(self):
        """
        Open webex app and typing meeting information
        """
        with action("啟動Webex應用程式", is_critical=True, setting=self.setting):
            subprocess.Popen([config.WEBEX_APP_PATH])

        time.sleep(5)

        with action(
            "按下[加入會議]按鈕，進入輸入頁面", is_critical=True, setting=self.setting
        ):
            main_window = Desktop(backend="uia").window(
                title="Webex", class_name="MainWindow"
            )
            logger.debug(main_window.exists())
            set_foreground(main_window)
            btn = main_window.child_window(
                title_re=" .*加入會議.*",
                control_type="Button",
            )

            if btn.exists(timeout=5):
                btn.wait("visible", timeout=3)
                try:
                    btn.iface_invoke.Invoke()
                except Exception:
                    btn.click_input()

    @deprecated("找不到webex url schema使用")
    def _launch_by_url(self):
        """
        使用內部 self.meeting_url 進入
        deprecated
        """
        with action("開啟Webex URL", setting=self.setting):
            webbrowser.open(self.meeting_url)

        time.sleep(5)

        with action("按下[加入會議]按鈕", setting=self.setting):
            waiting_window = Desktop(backend="uia").window(title_re=".*準備加入.*")
            waiting_window.set_focus()
            waiting_window.child_window(
                title_re=".*加入.*",
                control_type="Button",
            ).click_input()

    def _input_meeting_info(self):
        if self.meeting_url:
            with action("輸入URL", is_critical=True, setting=self.setting):
                copy_paste(self.meeting_url)

        else:
            with action("輸入ID/PW", is_critical=True, setting=self.setting):
                copy_paste(self.meeting_id)
                time.sleep(3)

                password_window = Desktop(backend="uia").window(
                    title="Webex", class_name="CiscoUIFrame"
                )

                set_foreground(password_window)

                time.sleep(3)
                copy_paste(self.password)

        time.sleep(3)

        with action("按下[加入會議]按鈕", is_critical=True, setting=self.setting):
            # waiting_window = Desktop(backend="uia").window(title_re=".*準備加入.*")
            # waiting_window.set_focus()
            # btn = waiting_window.child_window(
            #     title_re=".*加入.*",
            #     control_type="Button",
            # )
            # btn.wait("ready", timeout=60)
            # btn.click_input()
            pyautogui.press("enter")

    def _handle_waiting_room_and_change_layout(self):
        """
        處理進入會議後的版面切換
        Webex中多數元件有相同屬性，難以用程式辨認，因此直接點擊指定座標。
        """
        # time.sleep(5)
        with action(
            "點擊[版面配置]按鈕",
            setting=self.setting,
        ):
            hwnd = find_window_hwnd(
                f"{self.meeting_name}|meeting|Personal Room", timeout=30
            )
            if not hwnd:
                raise RuntimeError("找不到 Webex 會議視窗")

            meeting_window = Desktop(backend="uia").window(handle=hwnd)
            logger.info(f"window name {meeting_window.window_text()}")
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
            win32gui.SetForegroundWindow(hwnd)
            btn = meeting_window.child_window(
                title_re="版面配置",
                auto_id="ScannedByVDI",
                control_type="Button",
                found_index=0,
            )

            try:
                btn.wait("ready", timeout=config.MEETING_WAIT_TIMEOUT_IN_SECOND)
                btn.click_input()

            except Exception as e:
                raise TimeoutError(f"未出現[版面配置]，因為等待主持人允許超時, {e}")

        with action("選擇排版", setting=self.setting):
            attr_name = f"WEBEX_{self.layout.upper()}_POINT"
            point_str = getattr(config, attr_name, None)
            if point_str:
                x, y = self._parse_button_point(point_str)
                pyautogui.click(x, y)
            else:
                e = "Layout point is None, please check point setting"
                logger.warning(e)
                raise ValueError(e)

        with action("靜音", setting=self.setting):
            btn = meeting_window.child_window(
                title_re="(?<!取消)靜音.*",
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
