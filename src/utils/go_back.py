# src/views/base_window.py
from PyQt5.QtWidgets import QMainWindow

class BaseWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent

    def go_back_page(self):
        """Quay về parent window nếu có"""
        if self.parent:
            self.parent.show()
        self.close()
