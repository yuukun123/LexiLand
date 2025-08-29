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

        if parent:
            # Lấy hình chữ nhật (vị trí và kích thước) của cửa sổ cha
            parent_rect = parent.geometry()
            # Lấy hình chữ nhật của chính dialog này
            dialog_rect = self.geometry()

            # Tính toán vị trí x, y để dialog nằm ở giữa
            move_x = parent_rect.x() + (parent_rect.width() - dialog_rect.width()) // 2
            move_y = parent_rect.y() + (parent_rect.height() - dialog_rect.height()) // 2

            # Di chuyển dialog đến vị trí đã tính toán
            self.move(move_x, move_y)
            print(f"DEBUG: Di chuyển dialog đến vị trí ({move_x}, {move_y})")

        self.Cancel_Btn.clicked.connect(self.buttonController.handle_cancel)
