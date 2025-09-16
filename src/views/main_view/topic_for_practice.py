from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog

class topic_practice(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi("../UI/forms/Topic_for_practice.ui", self)
        # Thêm frameless + trong suốt
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(1.0)


        if parent:
            # Lấy hình chữ nhật (vị trí và kích thước) của cửa sổ cha
            parent_rect = parent.geometry()
            # Lấy hình chữ nhật của chính dialog này
            dialog_rect = self.geometry()
            print(f"DEBUG: PARENT RECT: {parent_rect}")
            print(f"DEBUG: DIALOG RECT: {dialog_rect}")
            # Tính toán vị trí x, y để dialog nằm ở giữa
            move_x = parent_rect.x() + (parent_rect.width() - dialog_rect.width()) // 2
            move_y = parent_rect.y() + (parent_rect.height() - dialog_rect.height()) // 2

            # Di chuyển dialog đến vị trí đã tính toán
            self.move(move_x, move_y)
            print(f"DEBUG: Di chuyển dialog đến vị trí ({move_x}, {move_y})")
