import logging
import subprocess
import sys
import time
from pathlib import Path

import obsws_python as obs
import psutil

if sys.platform == "win32":
    import win32gui
    from pywinauto import Desktop

from shared.config import config

from .utils import action, find_window_hwnd, kill_process

logger = logging.getLogger(__name__)


class OBSManager:
    PROCESS_NAME = "obs64.exe"

    def __init__(self):
        self.obs_path = config.OBS_PATH
        self.port = 4455

    def launch_obs(self):
        """
        不確定使用舊的process連線websocket會不會出錯
        """
        ## 可能導致殭屍程式，會讓下次OBS啟動失敗
        # if self._check_exist():
        # if self._check_exist_uia():
        #     logger.debug("OBS Exist")
        #     # 再次嘗試kill
        #     return

        with action("啟動 OBS", is_critical=True):
            subprocess.Popen(
                [str(self.obs_path)],
                cwd=Path(self.obs_path).resolve().parent,
            )
        # time.sleep(1)
        self._check_mode()

    def connect(self, retries=5, timeout=5):
        with action("連線 OBS", is_critical=True):
            for n in range(retries):
                try:
                    self.client = obs.ReqClient(
                        host="localhost",
                        port=self.port,
                        timeout=timeout,
                    )
                    if self._check_connect():
                        logger.debug(f"第{n + 1}次連線成功")
                        return

                except Exception:
                    logger.debug(f"第{n + 1}次連線失敗")
                    time.sleep(1)

            raise ConnectionError("連線 OBS 失敗")

    def kill_obs_process_by_psutil(self):
        """
        這個方法會讓OBS啟動時跳出，安全模式的提示框，不建議使用
        """
        with action("關閉OBS by psutil"):
            kill_process(process_name="obs64.exe")

    def kill_obs_process_by_taskkill(self):
        with action("關閉OBS by taskkill"):
            result = subprocess.run(
                ["taskkill", "/IM", "obs64.exe", "/T"],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                logger.debug("[安全]關閉OBS")
                return

            logger.debug(f"溫和關閉失敗 (代碼 {result.returncode})，嘗試強制關閉...")
            # !!! 如果強制關閉OBS，高機率導致下次錄影出錯 !!!
            subprocess.run(
                ["taskkill", "/F", "/IM", "obs64.exe", "/T"],
            )
            logger.warning("[強制]關閉OBS，下次啟動詢問是否使用安全模式")

    def setup_obs_scene(self, scene_name: str):
        with action(f"配置場景: {scene_name}", is_critical=True):
            self._check_connect()
            self.client.set_current_program_scene(scene_name)
            # TODO: audio check

    def setup_obs_window(self, meeting_name=None):
        """
        確保 OBS 錄製的視窗正確對應到當前的 Webex 會議。
        優先用 hwnd 精確比對，失敗再用關鍵字比對。
        """
        with action("更改obs中的錄製視窗", is_critical=False):
            resp = self.client.get_input_properties_list_property_items(
                "webex.exe", "window"
            )
            items = getattr(resp, "property_items", [])

            for item in items:
                logger.debug(f"OBS 視窗選項: {item['itemName']}")

            target_name = None
            target_value = None

            # 方法一：用 hwnd 取得精確標題比對
            hwnd = find_window_hwnd(
                f"{meeting_name}|meeting|Personal Room" if meeting_name else "CiscoCollabHost",
                timeout=10,
            )
            if hwnd:
                title = win32gui.GetWindowText(hwnd)
                logger.info(f"hwnd={hwnd}, 視窗標題: '{title}'")
                for item in items:
                    if title in item["itemName"]:
                        target_name = item["itemName"]
                        target_value = item["itemValue"]
                        break

            # 方法二：fallback 用關鍵字比對
            if not target_value:
                logger.info("hwnd 比對失敗，改用關鍵字比對")
                cand_win = [
                    (item["itemName"], item["itemValue"])
                    for item in items
                    if "CiscoCollabHost.exe".lower() in item["itemName"].lower()
                ]
                if cand_win:
                    target_name, target_value = max(cand_win, key=lambda x: len(x[0]))

            if not target_value:
                raise ValueError(
                    "找不到當前會議的 Webex 視窗。將維持上次的設定，可能導致錄製畫面全黑或錯誤。"
                )

            logger.info(f"設定 OBS 錄製視窗: {target_name}")
            self.client.set_input_settings(
                name="webex.exe",
                settings={"window": target_value},
                overlay=True,
            )

    def disconnect(self):
        with action("斷開 OBS 連線"):
            self._check_connect()
            self.client.disconnect()

    def start_recording(self):
        with action("啟動錄影", is_critical=True):
            self._check_connect()
            status = self.client.get_record_status()

            if status.output_active:  # type: ignore
                logger.warning("OBS 已經在錄影中，跳過啟動指令")
                return

            self.client.start_record()

    def stop_recording(self):
        with action("停止錄影"):
            self._check_connect()
            status = self.client.get_record_status()

            if not status.output_active:  # type: ignore
                logger.warning("OBS 目前並未錄影，跳過停止指令")
                return

            # duration_ms = status.output_duration  # type: ignore
            # hours, remainder = divmod(int(duration_ms / 1000), 3600)
            # minutes, seconds = divmod(remainder, 60)
            # logger.info(f"錄影時長: {hours:02d}:{minutes:02d}:{seconds:02d}")

            self.client.stop_record()

    def _check_connect(self) -> bool:
        """檢查並回傳連線物件，解決 'None' 的型別問題"""
        if self.client is None:
            raise ConnectionError("OBS WebSocket 未連線")

        try:
            self.client.get_version()
            return True

        except Exception:
            raise ConnectionError("OBS 連線已失效")

    def _check_mode(self):
        """監控並自動點擊 OBS 安全模式彈窗"""
        with action("檢查安全模式彈窗"):
            try:
                obs_window = Desktop(backend="uia").window(
                    title_re=".*偵測到 OBS Studio 當機.*|.*OBS Studio.*"
                )

                if obs_window.exists(timeout=5):
                    btn = obs_window.child_window(
                        title="以一般模式執行", control_type="Button"
                    )
                    if btn.exists():
                        btn.click()
                        logger.debug("已自動點擊『一般模式』。")

            except Exception as e:
                logger.debug(f"未發現彈窗或點擊失敗 (可忽略): {e}")

    def _check_exist(self):
        for proc in psutil.process_iter(["name"]):
            if proc.info["name"] == self.PROCESS_NAME:
                return True

    def _check_exist_uia(self):
        try:
            win = Desktop(backend="uia").window(title_re=".*OBS.*")
            win.wait("exists", timeout=5, retry_interval=1)
            return True

        except Exception:
            return False
