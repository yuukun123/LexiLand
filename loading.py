import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton
from PyQt5.QtCore import QTimer

# Import class LoadingOverlay của bạn
# Đảm bảo đường dẫn import là chính xác từ vị trí của file test này
from src.views.widgets.loading_overlay import LoadingOverlay


class TestWindow(QMainWindow):
    """Một cửa sổ chính đơn giản để làm nền cho loading overlay."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Loading Overlay")
        self.setGeometry(100, 100, 800, 600)  # Đặt kích thước cửa sổ

        # Thêm một nút để kích hoạt loading
        self.button = QPushButton("Show Loading for 3 seconds", self)
        self.button.setGeometry(300, 250, 200, 50)
        self.button.clicked.connect(self.show_loading_test)

        # Khởi tạo loading overlay
        self.loading = LoadingOverlay(self)

    def show_loading_test(self):
        print("Đang hiển thị loading overlay...")

        # Hiển thị và bắt đầu animation
        self.loading.start_animation()

        # Sử dụng QTimer để tự động ẩn loading sau 3 giây
        # QTimer an toàn hơn time.sleep() trong ứng dụng GUI
        QTimer.singleShot(3000, self.hide_loading_test)

    def hide_loading_test(self):
        print("Đang ẩn loading overlay...")
        self.loading.stop_animation()


if __name__ == '__main__':
    # Đoạn code boilerplate để chạy một ứng dụng PyQt
    app = QApplication(sys.argv)

    # Tạo và hiển thị cửa sổ test
    main_window = TestWindow()
    main_window.show()

    # Bắt đầu vòng lặp sự kiện
    sys.exit(app.exec_())