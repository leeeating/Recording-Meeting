from pywinauto.application import Application
from pywinauto.keyboard import send_keys
import pyperclip
import time
import win32gui
import win32api
import win32con
import win32process


def launch_cmd(cmd):
    send_keys('{LWIN down}r{LWIN up}')
    # run = Application().connect(title='執行', timeout=5)
    time.sleep(3)
    pyperclip.copy(cmd)
    # run.執行.type_keys('^v{ENTER}')
    send_keys('^v{ENTER}')

def call_from_search(keyword):
    send_keys('{LWIN}')
    time.sleep(0.3)

    pyperclip.copy(keyword)
    time.sleep(0.3)

    send_keys('^v')
    time.sleep(2)

    send_keys('{ENTER}')
    time.sleep(5)


def maximize_windows_with_title_and_executable(substring, executable_name):
    def window_enum_callback(hwnd, data):
        if not win32gui.IsWindowVisible(hwnd):
            return
        title = win32gui.GetWindowText(hwnd)
        # print(title)
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:
            process = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, pid)
            exe_name = win32process.GetModuleFileNameEx(process, 0)
            if substring in title and executable_name in exe_name:
                print(f"Maximizing window with title: {title} and executable: {exe_name}")
                win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
        except Exception as e:
            pass
            # print(f"Error: {e} {title}")

    win32gui.EnumWindows(window_enum_callback, None)

if __name__ == "__main__":
    maximize_windows_with_title_and_executable("Zoom", "Zoom.exe")
