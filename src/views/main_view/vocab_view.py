from PyQt5 import uic
from PyQt5.QtCore import Qt

from src.controllers.main_controller.topic_controller import TopicController
from src.controllers.main_controller.vocab_controller import VocabController
from src.utils.username_ui import set_user_info
from src.views.moveable_window import MoveableWindow
from src.controllers.buttonController import buttonController
from src.utils.go_back import BaseWindow

class VocabWindow(BaseWindow, MoveableWindow):
    def __init__(self, username, topic_id, parent=None):
        super().__init__(parent)
        uic.loadUi("../UI/forms/topic_word.ui", self)
        MoveableWindow.__init__(self)
        self.username = username
        self.topic_id = topic_id

        self.go_back.clicked.connect(self.go_back_page)

        # Thêm frameless + trong suốt
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(1.0)

        set_user_info(self.username_label, username)

        self.buttonController = buttonController(self)
        self.vocab_controller = VocabController(self, self.username, self.topic_id)
        self.vocab_controller.setup_for_user()

        self.closeBtn.clicked.connect(self.buttonController.handle_close)
        self.hideBtn.clicked.connect(self.buttonController.handle_hidden)
        self.logout.clicked.connect(self.buttonController.handle_logout)

        # self.Practice_btn.clicked.connect(self.vocab_controller.handle_add_vocabulary_click)
        # print("DEBUG: vocab button connected")