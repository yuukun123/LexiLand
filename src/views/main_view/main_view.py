from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QApplication

from src.services.query_data.query_data import QueryData
from src.views.main_view.practice_view import PracticeWindow
from src.views.main_view.topic_view import TopicWindow
from src.views.moveable_window import MoveableWindow
from src.views.main_view.practice_opt_view import topic_practice
from src.controllers.buttonController import buttonController
from src.utils.username_ui import set_user_info
from src.views.moveable_window import MoveableWindow
class MainWindow(QMainWindow, MoveableWindow):
    def __init__(self, username):
        # self.username = username
        super().__init__()
        uic.loadUi("UI/forms/main_screen.ui", self)
        MoveableWindow.__init__(self)

        self.go_back.hide()

        # Thêm frameless + trong suốt
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(1.0)

        self.query_data = QueryData()
        self._user_context = None
        self.load_user_context(username)

        if not self._user_context:
            QMessageBox.critical(self, "Lỗi nghiêm trọng", f"Không thể tìm thấy dữ liệu cho người dùng '{username}'.")
            return

        set_user_info(self.username_label, username)

        self.buttonController = buttonController(self)
        self.closeBtn.clicked.connect(buttonController.handle_close)
        self.hideBtn.clicked.connect(self.buttonController.handle_hidden)
        self.logout.clicked.connect(self.buttonController.handle_logout)

        self.vocab.clicked.connect(self.handle_topic_window_click)
        self.practice.clicked.connect(self.handle_practice_window_click)
        print("DEBUG: vocab button connected")

    def load_user_context(self, username):
        print(f"DEBUG: Đang tải user context cho username: {username}")
        self._user_context = self.query_data.get_user_by_username(username)
        print(f"DEBUG: User context đã tải: {self._user_context}")

    def handle_topic_window_click(self):
        print("DEBUG: start open_topic_window")
        if not self._user_context:
            # Sử dụng self._user_context để lấy username cho thông báo lỗi
            user_name_for_msg = self.username # Hoặc một giá trị mặc định
            QMessageBox.critical(self, "Lỗi nghiêm trọng", f"Không thể tìm thấy dữ liệu cho người dùng '{user_name_for_msg}'.")
            return
        try:
            self.hide()  # ẩn ngay lập tức
            current_username = self._user_context.get('user_name')
            self.topic_window = TopicWindow(parent=self, username=current_username, main_window=self)
            self.topic_window.topic_controller.setup_for_user(self._user_context)
            print("DEBUG: topic_window created", self.topic_window)
            self.topic_window.show()
            print("DEBUG: vocab_window show called")
        except Exception as e:
            print("ERROR while opening topic window:", e)
            self.show()

    def handle_practice_window_click(self):
        print("DEBUG: start open dialog topic_for_practice")
        dialog = topic_practice(self._user_context, self)
        dialog.open()


