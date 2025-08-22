from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow

from src.views.moveable_window import MoveableWindow
from src.controllers.buttonController import buttonController

class VocabWindow(QMainWindow, MoveableWindow):
    def __init__(self, username):
        self.username = username
        super().__init__()
        uic.loadUi("../UI/forms/vocab.ui", self)
        MoveableWindow.__init__(self)

        # self.go_back.hide()

        self.buttonController = buttonController(self)

        # Thêm frameless + trong suốt
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(1.0)

        self.username_label.setText(f"👤 {self.username}")

        self.buttonController = buttonController(self)

        self.closeBtn.clicked.connect(self.buttonController.handle_close)
        self.hideBtn.clicked.connect(self.buttonController.handle_hidden)
        self.logout.clicked.connect(self.buttonController.handle_logout)