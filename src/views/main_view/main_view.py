from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow

from src.views.moveable_window import MoveableWindow
from src.controllers.buttonController import buttonController

class MainWindow(QMainWindow, MoveableWindow):
    def __init__(self):
        # self.username = username
        super().__init__()
        uic.loadUi("../UI/forms/vocab.ui", self)

        # Thêm frameless + trong suốt
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setWindowOpacity(1.0)

        self.buttonController = buttonController(self)

        self.closeBtn.clicked.connect(self.buttonController.handle_close)
        self.hideBtn.clicked.connect(self.buttonController.handle_hidden)

