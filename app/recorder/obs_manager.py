import logging
import subprocess
import sys
import time
from pathlib import Path

import obsws_python as obs
import psutil

if sys.platform == "win32":
    from pywinauto import Desktop

from shared.config import config

from .utils import action, kill_process

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

        with action("啟動 OBS", logger, is_critical=True):
            subprocess.Popen(
                [str(self.obs_path)],
                cwd=Path(self.obs_path).resolve().parent,
            )
        # time.sleep(1)
        self._check_mode()

    def connect(self, retries=5, timeout=5):
        with action("連線 OBS", logger, is_critical=True):
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
        with action("關閉OBS by psutil", logger):
            kill_process(process_name="obs64.exe")

    def kill_obs_process_by_taskkill(self):
        with action("關閉OBS by taskkill", logger):
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
        with action(f"配置場景: {scene_name}", logger, is_critical=True):
            self._check_connect()
            self.client.set_current_program_scene(scene_name)
            # TODO: audio check

    def setup_obs_window(self, meeting_name=None):
        """
        確保 OBS 錄製的視窗正確對應到當前的 Webex 會議。
        Webex 視窗標題會隨 Host Name 更改，需動態搜尋並重新設定。
        """
        window_keyword = ["CiscoCollabHost.exe"]
        try:
            resp = self.client.get_input_properties_list_property_items(
                "webex.exe", "window"
            )

            items = getattr(resp, "property_items", [])

        except Exception as e:
            logger.error(f"無法獲取 OBS 來源 webex.exe 的屬性: {e}")
            raise

        target_value = None
        target_name = None

        cand_win = []
        for item in items:
            current_item_name = item["itemName"]
            current_item_value = item["itemValue"]

            print(current_item_name)
            print(current_item_value)
            print()

            have_keyword = any(
                keyword.lower() in current_item_name.lower()
                for keyword in window_keyword
            )

            if have_keyword:
                cand_win.append((current_item_name, current_item_value))

        with action("更改obs中的錄製視窗", logger, is_critical=False):
            if not cand_win:
                raise ValueError(
                    "找不到當前會議的 Webex 視窗。將維持上次的設定，可能導致錄製畫面全黑或錯誤。"
                )

            best_match = max(cand_win, key=lambda x: len(x[0]))
            target_name, target_value = best_match

            logger.info(f"Setting recording window to: {target_name}")

            self.client.set_input_settings(
                name="webex.exe",
                settings={"window": target_value},
                overlay=True,
            )

    def disconnect(self):
        with action("斷開 OBS 連線", logger):
            self._check_connect()
            self.client.disconnect()

    def start_recording(self):
        with action("啟動錄影", logger, is_critical=True):
            self._check_connect()
            status = self.client.get_record_status()

            if status.output_active:  # type: ignore
                logger.warning("OBS 已經在錄影中，跳過啟動指令")
                return

            self.client.start_record()

    def stop_recording(self):
        with action("停止錄影", logger):
            self._check_connect()
            status = self.client.get_record_status()

            if not status.output_active:  # type: ignore
                logger.warning("OBS 目前並未錄影，跳過停止指令")
                return

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
        with action("檢查安全模式彈窗", logger):
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
