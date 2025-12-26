import logging
import subprocess
import time
from pathlib import Path

import obsws_python as obs
from obsws_python.error import OBSSDKError
from pywinauto import Desktop

from shared.config import IS_WINDOWS, config

logger = logging.getLogger(__name__)


class OBSManager:
    def __init__(self):
        # self.client = None
        self.obs_path = config.OBS_PATH
        self.obs_cwd = config.OBS_CWD
        self.port = 4455

    def launch_obs(self):
        try:
            if IS_WINDOWS:
                process = subprocess.Popen(
                    [
                        str(self.obs_path),
                        "--unattended",
                        "--disable-shutdown-check",
                    ],
                    cwd=Path(self.obs_path).resolve().parent,
                )

                # 檢查進程是否立即崩潰
                if process.poll() is not None:
                    print("錯誤：OBS 啟動後立即結束，請檢查參數或路徑。")

            else:
                subprocess.Popen(["open", self.obs_path])
                logger.debug("OBS 已於 macOS 啟動")

        except Exception as e:
            logger.error(f"發生未知錯誤，無法啟動 OBS: {str(e)}")

        self._check_mode()

    def connect(self, retries=5):
        # for i in range(retries + 1):
        try:
            self.client = obs.ReqClient(host="localhost", port=self.port, timeout=120)
            logger.debug("OBS WebSocket 連線成功。")

        except Exception as e:
            # TODO: send email notification
            logger.warning(f"OBS連線失敗 ({e})")
            raise ConnectionError("OBS連線失敗")

    def kill_obs_process(self):
        """
        強制停止 OBS 進程。
        即便 OBS 未運行，此指令也會執行並由 stderr 吞掉報錯，確保冪等性。

        Test Case:
        [] A. OBS開啟，沒在錄影：必須確定websocket沒在連線
        [] B. OBS開啟，錄影中：
        [V] C. OBS完全關閉

        """
        if IS_WINDOWS:
            try:
                subprocess.run(
                    ["taskkill", "/IM", "obs64.exe", "/T"],
                    capture_output=True,
                    text=True,
                )
                logger.debug("[安全]關閉 OBS 進程。")

            except Exception:
                subprocess.run(
                    ["taskkill", "/F", "/IM", "obs64.exe", "/T"],
                    capture_output=True,
                    text=True,
                )
                logger.debug("[強制]關閉 Windows OBS 進程。")

        # for mac
        else:
            subprocess.run(
                ["pkill", "-9", "obs"],
                capture_output=True,
                check=False,
            )
            logger.debug("已嘗試強制清理 macOS OBS 進程。")

    def setup_obs_scene(
        self,
        scene_name: str,
        # audio_inputs: list,
    ):
        """配置錄影環境"""
        self.check_connect()

        try:
            self.client.set_current_program_scene(scene_name)
            time.sleep(2)
            # for source in audio_inputs:
            #     self.client.set_input_mute(source, False)
            #     time.sleep(1)

            logger.debug(f"Scene {scene_name} is ready with audio")
            return True

        except OBSSDKError as e:
            logger.error(f"Failed to setup scene: {e}")
            raise

    def disconnect(self):
        self.client.disconnect()

    def start_recording(self):
        self.check_connect()
        self.client.start_record()

    def stop_recording(self):
        self.check_connect()
        self.client.stop_record()

    def check_connect(self):
        """檢查當前 Client 是否可用"""
        try:
            self.client.get_version()

        except OBSSDKError:
            # TODO: send email notification
            logger.error("Disconnect to OBS WebSocket.")
            raise ConnectionError("OBS WebSocket 未連線")

    def _check_mode(self):
        """監控並自動點擊 OBS 安全模式彈窗"""
        try:
            app = Desktop(backend="uia")
            dialog = app.window(title_re=".*偵測到 OBS Studio 當機.*")

            if dialog.exists(timeout=5):
                btn = dialog.child_window(title="以一般模式執行", control_type="Button")
                btn.click()
                logger.debug("檢測到安全模式彈窗，已自動點擊『一般模式』。")

        except Exception:
            pass
