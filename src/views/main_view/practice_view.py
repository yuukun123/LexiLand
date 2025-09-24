from PyQt5 import uic
from PyQt5.QtCore import Qt

from src.controllers.main_controller.practice_controller import PracticeController
from src.utils.username_ui import set_user_info
from src.views.moveable_window import MoveableWindow
from src.controllers.buttonController import buttonController
from src.utils.go_back import BaseWindow

class PracticeWindow(BaseWindow, MoveableWindow):
    def __init__(self, username, topics, parent=None):
        super().__init__(parent)
        uic.loadUi("../UI/forms/practice.ui", self)
        MoveableWindow.__init__(self)
        self.username = username
        for t in topics:
            self.topic_name = t["name"]
            print(f"DEBUG: PRACTICE FOR TOPIC topic {self.topic_name} ")
        self.go_back.clicked.connect(self.go_back_page)

        # Thêm frameless + trong suốt
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(1.0)

        set_user_info(self.username_label, username)

        self.buttonController = buttonController(self)
        self.practice_controller = PracticeController(self)

        self.closeBtn.clicked.connect(self.buttonController.handle_close)
        self.hideBtn.clicked.connect(self.buttonController.handle_hidden)
        self.logout.clicked.connect(self.buttonController.handle_logout)
