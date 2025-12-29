import logging
import subprocess
import time
from pathlib import Path

import obsws_python as obs
from pywinauto import Desktop

from shared.config import config

from .utils import action, kill_process

logger = logging.getLogger(__name__)


class OBSManager:
    def __init__(self):
        # self.client = None
        self.obs_path = config.OBS_PATH
        self.obs_cwd = config.OBS_CWD
        self.port = 4455

    def launch_obs(self):
        with action("啟動 OBS", logger):
            subprocess.Popen(
                [str(self.obs_path)],
                cwd=Path(self.obs_path).resolve().parent,
            )
        # time.sleep(1)
        self._check_mode()

    def connect(self, retries=5, timeout=5):
        with action("連線 OBS", logger):
            for n in range(retries):
                try:
                    self.client = obs.ReqClient(
                        host="localhost",
                        port=self.port,
                        timeout=timeout,
                    )
                    self.client.get_version()
                    logger.debug(f"第{n + 1}次連線成功")
                    return

                except Exception:
                    logger.debug(f"第{n + 1}次連線失敗")
                    time.sleep(1)

            raise ConnectionError("連線 OBS 失敗")

    def kill_obs_process_by_psutil(self):
        self.disconnect()
        with action("關閉OBS", logger):
            kill_process(Pname="obs64.exe", logger=logger)

    def kill_obs_process_by_taskkill(self):
        with action("關閉OBS", logger):
            result = subprocess.run(
                ["taskkill", "/IM", "obs64.exe", "/T"],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                logger.debug("[安全]關閉OBS")
                return

            logger.debug(f"溫和關閉失敗 (代碼 {result.returncode})，嘗試強制關閉...")

            subprocess.run(
                ["taskkill", "/F", "/IM", "obs64.exe", "/T"],
            )
            logger.debug("[強制]關閉OBS，下次啟動詢問是否使用安全模式")

    def setup_obs_scene(self, scene_name: str):
        with action(f"配置場景: {scene_name}", logger):
            self.check_connect()
            self.client.set_current_program_scene(scene_name)
            # TODO: audio check

    def setup_obs_window(self):
        """
        確保每次OBS錄製的視窗，Webex的視窗名會隨者host name更改。\\
        先找到視窗名在重新設定錄製視窗
        """
        target_name = self._get_target_window_name()
        if target_name:
            with action("更改obs中的錄製視窗", logger):
                self.client.set_input_settings(
                    name="webex.exe",
                    settings={"window": target_name},
                    overlay=True,
                )
        else:
            logger.warning("找不到webex會議視窗，可能錄到其他視窗")

    def disconnect(self):
        if self.client:
            with action("斷開 OBS 連線", logger):
                self.client.disconnect()

        else:
            logger.warning(
                "OBS client isn't detecting. Can Not disconnect obs websocket"
            )

    def start_recording(self):
        with action("啟動錄影", logger):
            self.check_connect()
            status = self.client.get_record_status()

            if status.output_active:
                logger.warning("OBS 已經在錄影中，跳過啟動指令")
                return

            self.client.start_record()

    def stop_recording(self):
        with action("停止錄影", logger):
            self.check_connect()
            status = self.client.get_record_status()

            if not status.output_active:
                logger.warning("OBS 目前並未錄影，跳過停止指令")
                return

            self.client.stop_record()

    def check_connect(self) -> bool:
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

    @staticmethod
    def _get_target_window_name():
        windows = Desktop(backend="uia").windows()
        for win in windows:
            try:
                title = win.window_text()
                if "meeting" in title.lower() or "Webex" in title:
                    if title != "Webex":
                        class_name = win.class_name()
                        executable = "CiscoCollabHost.exe"

                        # 拼湊 OBS 5.x 要求的 window 字串格式
                        obs_window_str = f"{title}:{class_name}:{executable}"
                        return obs_window_str
            except Exception:
                continue
        return None
