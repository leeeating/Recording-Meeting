import logging
from contextlib import contextmanager

import psutil

from app.core.exceptions import ActionError


def kill_process(meeting_type: str, logger: logging.Logger):
    """
    這是非常重要的方法，可以保證下次視窗正常被偵測。
    """
    Pname = "Zoom.exe" if meeting_type == "ZOOM" else "CiscoCollabHost.exe"
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            if proc.info["name"] == Pname:
                logger.debug(
                    f"Terminating process: {proc.info['name']} (PID: {proc.info['pid']})"
                )
                proc.terminate()
                proc.wait()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass


@contextmanager
def action(action_name: str, logger: logging.Logger):
    """
    統一處理每步驟的error
    """
    logger.debug(f"開始執行操作: [{action_name}]")
    try:
        yield
        logger.info(f"成功執行操作: [{action_name}]")

    except Exception as e:
        logger.error(f"操作失敗 [{action_name}]: {e}")
        raise ActionError(f"操作失敗 [{action_name}]: {e}")
