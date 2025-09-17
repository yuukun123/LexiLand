from PyQt5.QtCore import Qt, QPoint, QSize, pyqtSignal
from PyQt5.QtWidgets import QApplication


class MoveableWindow:
    size_state_changed = pyqtSignal(bool)

    def __init__(self):
        self._old_pos = None
        self._is_mouse_pressed = False
        self.resize_on_drag_enabled = False
        self.is_mini_size = False
        self.mini_size = QSize(1434, 854)
        self._original_geometry = None

    def setResizeOnDrag(self, enabled: bool, mini_size: QSize = None):
        self.resize_on_drag_enabled = enabled
        if mini_size:
            self.mini_size = mini_size

    def mousePressEvent(self, event):
        # --- THÊM KIỂM TRA MỚI ---
        # Nếu cửa sổ đang được phóng to tối đa, bỏ qua sự kiện nhấn chuột trái
        if self.isMaximized():
            return
        # --- KẾT THÚC KIỂM TRA MỚI ---

        if event.button() == Qt.LeftButton:
            self._old_pos = event.globalPos()
            self._is_mouse_pressed = True
            if self.resize_on_drag_enabled and not self.is_mini_size:
                self._original_geometry = self.geometry()

    def mouseMoveEvent(self, event):
        # --- THÊM KIỂM TRA MỚI ---
        # Nếu cửa sổ đang được phóng to tối đa, bỏ qua sự kiện di chuyển chuột
        if self.isMaximized():
            return
        # --- KẾT THÚC KIỂM TRA MỚI ---

        if not self._is_mouse_pressed:
            return

        delta = event.globalPos() - self._old_pos

        # Logic thu nhỏ về mini-size khi kéo (giữ nguyên)
        if self.resize_on_drag_enabled and not self.is_mini_size:
            if delta.manhattanLength() > 5:
                current_center = self.geometry().center()
                self.is_mini_size = True
                self.resize(self.mini_size)

                new_geometry = self.frameGeometry()
                new_geometry.moveCenter(current_center)
                self.move(new_geometry.topLeft())

                self.size_state_changed.emit(True)

        # Logic di chuyển cửa sổ
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self._old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self._is_mouse_pressed = False

    def invisible(self):
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

