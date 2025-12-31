from PyQt6.QtCore import QThread, pyqtSignal


class ApiWorker(QThread):
    """
    Create new thread to handle API requests without blocking the GUI.
    """

    success = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, api_func, *args, **kwargs):
        super().__init__()
        self.api_func = api_func  # 要執行的 API 方法，例如 api_client.create_meeting
        self.args = args  # 傳給 API 的參數 (如 meeting_data)
        self.kwargs = kwargs

    def run(self):
        try:
            # 執行耗時的網路操作
            result = self.api_func(*self.args, **self.kwargs)
            self.success.emit(result)

        except Exception as e:
            # 捕捉所有錯誤並發射
            self.error.emit(str(e))
