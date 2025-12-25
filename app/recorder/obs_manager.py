import logging
import subprocess
import time

import obsws_python as obs
from obsws_python.error import OBSSDKError

from shared.config import IS_WINDOWS, config

logger = logging.getLogger(__name__)


class OBSManager:
    def __init__(self):
        # self.client = None
        self.obs_path = config.OBS_PATH
        self.obs_cwd = config.OBS_CWD
        self.port = 4455

    def launch_obs(self) -> bool:
        self._force_stop_obs()

        try:
            if IS_WINDOWS:
                # Windows 必須設定 cwd，否則 OBS 可能找不到插件或設定檔
                subprocess.Popen([self.obs_path], cwd=self.obs_cwd)
                logger.debug(f"OBS 已於 Windows 啟動，路徑: {self.obs_path}")

            else:
                subprocess.Popen(["open", self.obs_path])
                logger.debug("OBS 已於 macOS 啟動")

            time.sleep(5)
            return True

        except Exception as e:
            logger.error(f"發生未知錯誤，無法啟動 OBS: {str(e)}")

        return False

    def connect(self, retries=5) -> bool:
        for i in range(retries):
            try:
                self.client = obs.ReqClient(
                    host="localhost",
                    port=self.port,
                )
                logger.debug("OBS WebSocket 連線成功。")
                return True

            except Exception as e:
                # TODO: send email notification
                logger.warning(f"連線失敗，正在嘗試第 {i + 1} 次重試... ({e})")

            finally:
                time.sleep(5)

        return False

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

    def start_recording(self):
        self.check_connect()
        self.client.start_record()

    def stop_recording(self):
        self.check_connect()
        return self.client.stop_record()

    def check_connect(self):
        """檢查當前 Client 是否可用"""
        try:
            self.client.get_version()

        except OBSSDKError:
            # TODO: send email notification
            logger.warning("Disconnect to OBS WebSocket.", extra={"send_email": True})
            raise ConnectionError("OBS WebSocket 未連線")

    def _force_stop_obs(self):
        """
        強制停止 OBS 進程。
        即便 OBS 未運行，此指令也會執行並由 stderr 吞掉報錯，確保冪等性。
        """
        if IS_WINDOWS:
            # /F: 強制結束, /IM: 映像名稱, /T: 結束子進程
            # capture_output=True 會捕獲輸出，避免報錯訊息直接噴在終端機
            subprocess.run(
                ["taskkill", "/F", "/IM", "obs64.exe", "/T"],
                capture_output=True,
                text=True,
                check=False,  # 即使找不到進程也不拋出異常
            )
            logger.debug("已嘗試強制清理 Windows OBS 進程。")

        else:
            subprocess.run(["pkill", "-9", "obs"], capture_output=True, check=False)
            logger.debug("已嘗試強制清理 macOS OBS 進程。")

        time.sleep(2)
