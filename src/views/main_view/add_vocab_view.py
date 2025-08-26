from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog

from src.controllers.buttonController import buttonController
from src.views.moveable_window import MoveableWindow


class AddWordDialog(QDialog, MoveableWindow):
    def __init__(self, username, parent=None):
        super().__init__(parent)
        uic.loadUi("../UI/forms/add_vocabulary.ui", self)
        MoveableWindow.__init__(self)
        self.username = username

        self.buttonController = buttonController(self)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
