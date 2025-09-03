import win32gui
import win32con
import win32process
import win32api
import sys

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
    if len(sys.argv) > 1:
        maximize_windows_with_title_and_executable(sys.argv[1], sys.argv[2])
