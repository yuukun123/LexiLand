from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QMessageBox

from src.models.query_data.query_data import QueryData
from src.views.main_view.topic_view import TopicWindow
from src.views.moveable_window import MoveableWindow
from src.controllers.buttonController import buttonController
from src.utils.username_ui import set_user_info

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

        self.query_data = QueryData()
        self._user_context = None
        self.load_user_context(username)

        if not self._user_context:
            QMessageBox.critical(self, "Lỗi nghiêm trọng", f"Không thể tìm thấy dữ liệu cho người dùng '{username}'.")
            return

        set_user_info(self.username_label, username)

        self.buttonController = buttonController(self)
        self.closeBtn.clicked.connect(self.buttonController.handle_close)
        self.hideBtn.clicked.connect(self.buttonController.handle_hidden)
        self.logout.clicked.connect(self.buttonController.handle_logout)

        self.vocab.clicked.connect(self.open_vocab_window_click)
        print("DEBUG: vocab button connected")

    def load_user_context(self, username):
        print(f"DEBUG: Đang tải user context cho username: {username}")
        self._user_context = self.query_data.get_user_by_username(username)
        print(f"DEBUG: User context đã tải: {self._user_context}")

    def open_vocab_window_click(self):
        from src.windows.window_manage import open_vocab_window
        print("DEBUG: start open_vocab_window")

        if not self._user_context:
            # Sử dụng self._user_context để lấy username cho thông báo lỗi
            user_name_for_msg = self.username # Hoặc một giá trị mặc định
            QMessageBox.critical(self, "Lỗi nghiêm trọng", f"Không thể tìm thấy dữ liệu cho người dùng '{user_name_for_msg}'.")
            return
        try:
            self.hide()  # ẩn ngay lập tức
            current_username = self._user_context.get('user_name')
            self.vocab_window = TopicWindow(username=current_username, parent=self)
            self.vocab_window.vocab_controller.setup_for_user(self._user_context)
            print("DEBUG: vocab_window created", self.vocab_window)
            self.vocab_window.show()
            print("DEBUG: vocab_window show called")
        except Exception as e:
            print("ERROR while opening vocab window:", e)
            self.show()

