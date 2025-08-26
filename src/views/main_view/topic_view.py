from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QSizePolicy

from src.controllers.main_controller.topic_controller import VocabController
from src.views.moveable_window import MoveableWindow
from src.controllers.buttonController import buttonController
from src.utils.go_back import BaseWindow

class VocabWindow(BaseWindow, MoveableWindow):
    def __init__(self, username, parent=None):
        super().__init__(parent)
        uic.loadUi("../UI/forms/topic.ui", self)
        MoveableWindow.__init__(self)
        self.username = username

        self.go_back.clicked.connect(self.go_back_page)

        # Thêm frameless + trong suốt
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(1.0)

        self.username_label.setText(f"👤 {self.username}")

        self.buttonController = buttonController(self)
        self.vocab_controller = VocabController(self)

        self.closeBtn.clicked.connect(self.buttonController.handle_close)
        self.hideBtn.clicked.connect(self.buttonController.handle_hidden)
        self.logout.clicked.connect(self.buttonController.handle_logout)