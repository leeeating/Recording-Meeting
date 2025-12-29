import logging
import time
from contextlib import contextmanager

import psutil
import pyautogui
import pyperclip

from app.core.exceptions import ActionError


def copy_paste(info: str):
    pyperclip.copy(info)
    pyautogui.hotkey("ctrl", "v")
    pyautogui.press("enter")
    time.sleep(1)


def kill_process(Pname: str | None, logger: logging.Logger):
    """
    這是非常重要的方法，可以保證下次視窗正常被偵測。
    """
    for proc in psutil.process_iter(["pid", "name"]):
        if proc.info["name"] == Pname:
            logger.debug(
                f"Terminating process: {proc.info['name']} (PID: {proc.info['pid']})"
            )
            proc.terminate()
            proc.wait(10)


@contextmanager
def action(action_name: str, logger: logging.Logger):
    """
    統一處理每步驟的error
    """
    logger.debug(f"開始執行 [{action_name}] 操作")
    try:
        yield
        logger.info(f"成功執行 [{action_name}] 操作")

    except Exception as e:
        logger.error(f"操作 [{action_name}] 失敗 {e}")
        raise ActionError(f"操作 [{action_name}] 失敗, {e}")
