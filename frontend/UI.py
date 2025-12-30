import sys

from PyQt6.QtWidgets import QApplication

from frontend.GUI.main_window import MainWindow


def load_qss_style(filepath: str) -> str:
    """Load QSS style from a file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"QSS file not found: {filepath}")
        return ""


def main():
    app = QApplication(sys.argv)

    # 載入樣式
    QSS_FILEPATH = "frontend/GUI/style.qss"
    app.setStyleSheet(load_qss_style(QSS_FILEPATH))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
