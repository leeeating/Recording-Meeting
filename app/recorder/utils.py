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

def kill_process(process_name):
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] == process_name:
                # 獲取主進程與所有子進程
                parent = psutil.Process(proc.info['pid'])
                children = parent.children(recursive=True)
                
                # 2. 先溫和停止子進程，最後才是父進程
                for child in children:
                    child.terminate()
                parent.terminate()
                
                # 3. 等待一段時間讓資源釋放 (最多等 5 秒)
                gone, alive = psutil.wait_procs([parent] + children, timeout=5)
                
                # 4. 如果還有活著的，就強制殺掉
                for survivor in alive:
                    survivor.kill()
                    
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue



@contextmanager
def action(
    action_name: str,
    logger: logging.Logger,
    is_critical=False,
):
    """
    統一處理每步驟的error
    """
    logger.debug(f"開始執行 [{action_name}] 操作")
    try:
        yield
        logger.info(f"成功執行 [{action_name}] 操作")

    except Exception as e:
        if is_critical:
            logger.critical(f"重大操作 [{action_name}] 失敗: {e}", exc_info=True)
            raise ActionError(f"操作 [{action_name}] 失敗, {e}") from e

        else:
            logger.error(f"操作 [{action_name}] 失敗 {e}")
