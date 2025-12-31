from functools import partial

from PyQt6.QtWidgets import QWidget

from frontend.GUI.events import BottomBar
from frontend.services.api_client import ApiWorker


class BasePage(QWidget):
    def run_task(
        self,
        api_func,
        *args,
        success_msg="操作成功",
        callback=None,
        lock_widget=None,
        **kwargs,
    ):
        """自動封裝 Worker 並連接訊號"""
        BottomBar.update_status.emit("🚀 處理中...", 0)
        if lock_widget:
            lock_widget.setEnabled(False)

        worker = ApiWorker(api_func, *args, **kwargs)

        worker.success.connect(
            partial(
                self._on_base_success,
                success_msg=success_msg,
                callback=callback,
                lock_widget=lock_widget,
            )
        )
        worker.error.connect(partial(self._on_base_error, lock_widget=lock_widget))

        worker.start()
        self._worker_ref = worker

    def _on_base_success(self, result, success_msg, callback, lock_widget):
        BottomBar.update_status.emit(f"✅ {success_msg}", 2000)
        if lock_widget:
            lock_widget.setEnabled(True)

        if callback:
            # 支援帶參數或不帶參數的 callback
            try:
                callback(result)
            except TypeError:
                callback()

    def _on_base_error(self, err_msg, lock_widget):
        BottomBar.update_status.emit(f"❌ 錯誤: {err_msg}", 0)
        if lock_widget:
            lock_widget.setEnabled(True)
