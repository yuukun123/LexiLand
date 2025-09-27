from PyQt5 import uic
from PyQt5.QtCore import Qt, pyqtSignal
from src.models.query_data.query_data import QueryData
from src.controllers.main_controller.vocab_controller import VocabController
from src.utils.username_ui import set_user_info
from src.views.moveable_window import MoveableWindow
from src.controllers.buttonController import buttonController
from src.utils.go_back import BaseWindow

class VocabWindow(BaseWindow, MoveableWindow):
    # signal if have change data
    data_changed = pyqtSignal()

    def __init__(self, username, topic_id, pre_window, parent=None):
        super().__init__(parent)
        uic.loadUi("../UI/forms/topic_word.ui", self)
        MoveableWindow.__init__(self)
        self.username = username
        self.topic_id = topic_id
        self.querydata = QueryData()

        self.pre_window = pre_window

        self.go_back.clicked.connect(self.go_back_page)

        # Thêm frameless + trong suốt
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(1.0)

        set_user_info(self.username_label, username)

        self.buttonController = buttonController(self)
        self.vocab_controller = VocabController(self, self.username, self.topic_id)

        self.closeBtn.clicked.connect(self.buttonController.handle_close)
        self.hideBtn.clicked.connect(self.buttonController.handle_hidden)
        self.logout.clicked.connect(self.buttonController.handle_logout)

        self.Practice_btn.clicked.connect(self.vocab_controller.handle_open_practice_click)
        # print("DEBUG: vocab button connected")

    def go_back_to_previous(self):
        """Hàm này bây giờ sẽ quay lại đúng cửa sổ đã gọi nó."""
        # signal before close
        self.data_changed.emit()

        if self.previous_window:
            self.previous_window.show()  # Hiển thị lại TopicWindow
        self.close()  # Đóng cửa sổ hiện tại (DetailTopicWindow)
