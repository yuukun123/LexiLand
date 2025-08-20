from PyQt5.QtWidgets import QApplication
import sys
from src.windows.window_manage import open_login_window, open_main_window

if __name__ == "__main__":
    app = QApplication(sys.argv)
    open_login_window()
    # open_main_window()
    sys.exit(app.exec_())

