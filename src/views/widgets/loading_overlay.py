import os

from PyQt5 import uic
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtWidgets import QDialog
from PyQt5.QtGui import QMovie
from resources import resources_rc

class LoadingOverlay(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi("UI/forms/loading_overlay.ui", self)

        # Đảm bảo widget này sẽ che phủ toàn bộ widget cha
        # if parent:
        #     self.setGeometry(0, 0, parent.width(), parent.height())
        #
        # # Thiết lập và chạy ảnh GIF
        # gif_path = os.path.join(os.path.dirname(__file__), "..", "..", "UI", "icons", "loading.gif")
        # self.movie = QMovie(gif_path)
        # self.gif_label.setMovie(self.movie)
        #
        # self.hide()  # Mặc định là ẩn

        # self.design_size = self.size()
        # print(f"DEBUG: Kích thước thiết kế của LoadingOverlay là: {self.design_size.width()}x{self.design_size.height()}")

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Đặt dialog là "modal", nó sẽ chặn tương tác với cửa sổ cha
        self.setModal(True)

        # Thiết lập và chạy ảnh GIF
        # (Giữ nguyên code QMovie của bạn)
        self.movie = QMovie(":/UI/icons/loading.gif")
        self.gif_label.setMovie(self.movie)

    def center_on_parent(self):
        """Hàm riêng để thực hiện logic căn giữa."""
        if self.parent():
            parent_rect = self.parent().geometry()
            dialog_size = self.sizeHint()

            move_x = parent_rect.x() + (parent_rect.width() - dialog_size.width()) // 2
            move_y = parent_rect.y() + (parent_rect.height() - dialog_size.height()) // 2

            # In ra để debug
            print(f"DEBUG: Căn giữa LoadingOverlay. Parent geo: {parent_rect}, Dialog hint: {dialog_size}. Di chuyển đến ({move_x}, {move_y})")
            self.move(move_x, move_y)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self.center_on_parent)

    def start_animation(self):
        """Hàm này giờ chỉ cần bắt đầu animation và hiển thị."""
        self.movie.start()
        self.open()

    def stop_animation(self):
        """Dừng animation và đóng dialog."""
        self.movie.stop()
        self.accept()
