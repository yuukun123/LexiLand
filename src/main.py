from PyQt5.QtWidgets import QApplication
import sys
from src.windows.window_manage import open_login_window

if __name__ == "__main__":
    app = QApplication(sys.argv)
    open_login_window()
    # window = open_addChar_window()
    # window = open_listStd_window("admin")
    # window = open_addNew_window()
    sys.exit(app.exec_())