from PyQt6.QtCore import QObject, pyqtSignal


class StatueBar(QObject):
    """
    全局狀態列
    """

    update_status = pyqtSignal([str, int])  # message, duration (ms)


BottomBar = StatueBar()
