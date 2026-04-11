from functools import partial

from PyQt6.QtCore import QThreadPool
from PyQt6.QtWidgets import QMessageBox, QWidget

from frontend.GUI.events import BottomBar
from frontend.services.api_client import ApiWorker


class BasePage(QWidget):
    def run_request(
        self,
        api_func,
        *args,
        name="Api Request",
        callback=None,
        lock_widget=None,
        error_title: str | None = None,
        error_suffix: str | None = None,
        **kwargs,
    ):
        """
        使用ApiWorker在新線程中執行API請求
        """
        BottomBar.update_status.emit("🚀 處理中...", 0)
        if lock_widget:
            lock_widget.setEnabled(False)

        worker = ApiWorker(api_func, name, *args, **kwargs)

        worker.signal.success.connect(
            partial(
                self._on_success,
                callback=callback,
                lock_widget=lock_widget,
            )
        )
        worker.signal.error.connect(
            partial(
                self._on_error,
                callback=callback,
                lock_widget=lock_widget,
                error_title=error_title,
                error_suffix=error_suffix,
            )
        )

        pool = QThreadPool.globalInstance()

        if pool is not None:
            pool.start(worker)
        else:
            raise RuntimeError("無法獲取 QThreadPool 實例")

    def _on_success(self, result, success_msg, callback, lock_widget):
        self._on_request_complete(result, success_msg, callback, lock_widget)

    def _on_error(
        self, err_msg, callback, lock_widget, error_title=None, error_suffix=None
    ):
        if error_title:
            display_msg = f"{err_msg}\n\n{error_suffix}" if error_suffix else err_msg
            QMessageBox.warning(self, error_title, display_msg)
        self._on_request_complete(None, err_msg, callback, lock_widget)

    def _on_request_complete(self, result, msg, callback, lock_widget):
        """統一處理請求完成（成功或失敗）"""
        BottomBar.update_status.emit(msg, 2)
        if lock_widget:
            lock_widget.setEnabled(True)

        if callback:
            try:
                callback(result)
            except TypeError:
                callback()
