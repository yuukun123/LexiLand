from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow

from src.views.moveable_window import MoveableWindow
from src.controllers.buttonController import buttonController

class MainWindow(QMainWindow, MoveableWindow):
    def __init__(self, username):
        self.username = username
        super().__init__()
        uic.loadUi("../UI/forms/main_screen.ui", self)
        MoveableWindow.__init__(self)

        self.go_back.hide()

        # Thêm frameless + trong suốt
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(1.0)

        self.username_label.setText(f"👤 {self.username}")

        self.buttonController = buttonController(self)

        self.closeBtn.clicked.connect(self.buttonController.handle_close)
        self.hideBtn.clicked.connect(self.buttonController.handle_hidden)
        self.logout.clicked.connect(self.buttonController.handle_logout)

        print("DEBUG: vocab button connected")
        self.vocab.clicked.connect(lambda: self.open_vocab_window_click(username))

    def open_vocab_window_click(self, username):
        from src.windows.window_manage import open_vocab_window
        print("DEBUG: start open_vocab_window")
        try:
            self.hide()  # ẩn ngay lập tức
            self.vocab_window = open_vocab_window(username, parent=self)
            print("DEBUG: vocab_window created", self.vocab_window)
            self.vocab_window.show()
            print("DEBUG: vocab_window show called")
        except Exception as e:
            print("ERROR while opening vocab window:", e)

