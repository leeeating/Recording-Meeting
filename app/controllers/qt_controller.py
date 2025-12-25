import logging
from PyQt6.QtCore import (
    QRunnable,
    QObject,
    pyqtSignal,
    QThreadPool,
    pyqtSlot,
    QCoreApplication,
    QThread,
)
from sqlalchemy.orm import Session
from typing import Callable

from app.core.scheduler import create_scheduler
from app.services.meeting_service import MeetingService
from app.models.schemas import MeetingCreateSchema
from app.services.task_service import TaskService
from frontend.events import UISignals
from frontend.GUI.main_window import MainWindow

controller_logger = logging.getLogger(__name__)


# --- A. 輔助類別: Worker Signals (用於跨線程發送結果) ---
class WorkerSignals(QObject):
    """定義 DbWorker 執行結果的信號。"""

    finished = pyqtSignal()  # 任務完成（無論成功或失敗）
    error = pyqtSignal(str)  # 發生異常，攜帶錯誤訊息 (str)
    result = pyqtSignal(object)  # 成功完成，攜帶結果對象


# --- B. 輔助類別: DB Worker (核心線程隔離邏輯) ---
class DbWorker(QRunnable):
    """
    用於在 QThreadPool 背景線程中執行所有耗時的數據庫事務。
    繼承 QRunnable，不需要手動管理線程的生命週期。
    """

    def __init__(self, db: Session, service_method: Callable, data: object):
        super().__init__()
        self.db = db
        # 接收一個可執行的 Service 方法
        self.service_method = service_method
        self.data = data
        self.signals = WorkerSignals()
        self.logger = controller_logger

    @pyqtSlot()
    def run(self):
        """此方法將在背景線程中執行，包含事務控制。"""
        try:
            # 1. 執行 Service 邏輯
            result = self.service_method(self.db, self.data)

            self.db.commit()

            self.signals.result.emit(result)

        except Exception as e:
            self.db.rollback()
            error_msg = f"DB事務錯誤: {type(e).__name__} - {str(e)}"
            self.signals.error.emit(error_msg)
            self.logger.error(error_msg)

        finally:
            self.db.close()
            self.signals.finished.emit()


# --- C. AppController 主類別 (主線程執行) ---
class AppController(QObject):
    """應用程式的核心協調者，負責初始化服務、連接信號和管理事務。"""

    # 定義 Controller 內部用於回饋 UI 的信號 (例如，通知表格需要刷新)
    # 這是 Service -> Controller -> View 的傳輸通道
    data_changed = pyqtSignal()

    def __init__(
        self,
        main_window: MainWindow,
        db_session_factory: Callable[[], Session],
        ui_signals: UISignals,
    ):
        super().__init__()

        self.db_session_factory = db_session_factory()
        self.main_window = main_window
        self.thread_pool = QThreadPool.globalInstance()
        self.scheduler = create_scheduler()

        self.task_service = TaskService(
            db=self.db_session_factory, scheduler=self.scheduler
        )
        self.meeting_service = MeetingService(
            db=self.db_session_factory, task_service=self.task_service
        )

        # 啟動排程器 (在它自己的背景線程中運行)
        self.scheduler.start()

        # 建立信號連接
        self._wire_up_signals(ui_signals)
        print("✅ AppController 服務啟動完成 (PyQt6 兼容)。")

    def _wire_up_signals(self, ui_signals: UISignals):
        """將 UI 組件的信號連接到 Controller 的處理槽。"""
        # 1. 連接 UI 事件 (View -> Controller)
        # 假設 UI 信號的實例儲存在 ui_signals.meeting_page 中
        ui_signals.meeting_page.save_requested.connect(self.handle_meeting_save)

        # 2. 連接 Controller 結果信號 (Controller -> View)
        # 這是 Controller 告訴 UI 刷新的通道
        self.data_changed.connect(self.main_window.refresh_data)

    # --- 槽 (Slot) 實作: 接收 UI 事件並啟動 Worker ---
    @pyqtSlot(MeetingCreateSchema)
    def handle_meeting_save(self, meeting_data: MeetingCreateSchema):
        """
        接收來自 UI 的保存會議信號，並啟動 DbWorker 處理。
        此方法在主線程中執行。
        """
        self.main_window.show_status("正在處理會議排程，請稍候...")

        # 1. 取得新的 DB Session
        db_session = self.db_session_factory

        # 2. 創建 DbWorker 實例 (指定要執行的 Service 方法)
        worker = DbWorker(
            db=db_session,
            service_method=self.meeting_service.create_meeting_and_task,
            data=meeting_data,
        )

        # 3. 連接 Worker 的結果信號給 Controller 的回饋槽 (確保在主線程執行)
        worker.signals.result.connect(self._on_meeting_save_success)
        worker.signals.error.connect(self._on_meeting_save_error)

        # 4. 將 Worker 提交給線程池執行
        self.thread_pool.start(worker)

    # --- 槽 (Slot) 實作: 處理 Worker 回饋 ---
    @pyqtSlot(object)
    def _on_meeting_save_success(self, result_schema):
        """
        Worker 成功完成任務後，此槽在主線程中被調用。
        """
        # 1. 通知 UI 顯示成功訊息
        self.main_window.show_success_message(
            f"會議創建與排程成功！ID: {result_schema.id}"
        )

        # 2. 發射信號，通知所有相關 UI 介面更新數據 (例如刷新表格)
        self.data_changed.emit()

    @pyqtSlot(str)
    def _on_meeting_save_error(self, error_msg):
        """
        Worker 發生錯誤後，此槽在主線程中被調用。
        """
        # 通知 UI 顯示錯誤訊息
        self.main_window.show_error_message(f"操作失敗: {error_msg}")

    # --- 應用程式關閉時的清理方法 ---
    def shutdown(self):
        """優雅地關閉排程器和線程池。"""
        print("Shutting down services...")
        # 停止排程器
        self.scheduler.shutdown(wait=False)
        # 等待線程池中的任務完成，設置超時時間
        self.thread_pool.waitForDone(1000)
        print("Services shut down gracefully.")
