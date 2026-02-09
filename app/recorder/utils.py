import logging
import time
from contextlib import contextmanager

import psutil
import pyautogui
import pyperclip
import win32con
import win32gui

from app.core.exceptions import ActionError

logger = logging.getLogger(__name__)


def maximize_window(window_spec):
    """
    高度穩定的視窗最大化與聚焦方法
    """
    if not window_spec.exists(timeout=10):
        logger.error("錯誤：找不到指定視窗")
        return False

    wrapper = window_spec.wrapper_object()
    print(wrapper)
    hwnd = wrapper.handle

    # 1. 處理 Handle 存在的情況（使用 Win32 API 最穩定）
    if hwnd:
        # 如果視窗目前是最小化，先還原
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            time.sleep(0.5)

        # 執行最大化 (SW_MAXIMIZE = 3)
        win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
        logger.info(f"已透過 Win32 強制最大化 Handle: {hwnd}")
    
    # 2. 處理無 Handle 或 Win32 失效（備案：UIA 模式）
    else:
        try:
            wrapper.maximize()
            logger.info("已透過 UIA 模式最大化")
        except Exception as e:
            logger.error(f"UIA 最大化失敗: {e}")

    # 3. 關鍵：等待 UI 重繪完成
    # 最大化後視窗座標會劇烈變動，必須等待 ready
    window_spec.wait("ready", timeout=5)
    wrapper.set_focus()
    
    # 額外保險：確保視窗真的在最前面
    if hwnd:
        win32gui.SetForegroundWindow(hwnd)

    return True

def set_foreground(window):
    if not window.exists():
        logger.info("視窗不存在")
        return

    wrapper = window.wrapper_object()
    hwnd = wrapper.handle

    # --- 邏輯 A：如果有實體 Handle (HWND) ---
    if hwnd:
        try:
            # 檢查是否最小化
            if win32gui.IsIconic(hwnd):
                logger.info("視窗最小化中，正在還原...")
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

            # 強制推到最前方
            win32gui.SetForegroundWindow(hwnd)
            logger.info(f"已透過 HWND ({hwnd}) 置頂視窗")

        except Exception as e:
            logger.info(f"Win32 置頂失敗，嘗試備案: {e}")
            wrapper.set_focus()  # 失敗時切換回 UIA 原生方法

    # --- 邏輯 B：如果沒有 Handle (無柄元件) ---
    else:
        logger.info("此元件無實體 Handle，使用 UIA set_focus")
        try:
            wrapper.set_focus()
        except Exception as e:
            logger.info(f"UIA set_focus 也失敗: {e}")


def copy_paste(info: str):
    pyperclip.copy(info)
    pyautogui.hotkey("ctrl", "v")
    pyautogui.press("enter")
    time.sleep(1)


def kill_process(process_name):
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            if proc.info["name"] == process_name:
                # 獲取主進程與所有子進程
                parent = psutil.Process(proc.info["pid"])
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
    meeting_name: str = "",
    meeting_type: str = "",
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
            logger.critical(f"重大操作: {action_name} 失敗: {e}", exc_info=True)
            raise ActionError(f"操作 [{action_name}] 失敗, {e}") from e

        else:
            logger.error(
                f"操作 [{action_name}] 失敗: {e}",
                extra={
                    "send_email": True,
                    "meeting_name": meeting_name,
                    "meeting_type": meeting_type,
                },
            )
