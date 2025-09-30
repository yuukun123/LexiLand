# trong src/controllers/base_controller.py
from abc import ABC, abstractmethod
from PyQt5.QtCore import pyqtSignal, QObject, QThread
from PyQt5.QtWidgets import QApplication
from src.services.query_data.query_data import QueryData
from src.views.widgets.loading_overlay import LoadingOverlay

import time

class DataWorker(QObject):
    finished = pyqtSignal()
    # Tín hiệu mới: mang theo kết quả đã được tải
    stats_ready = pyqtSignal(dict)
    items_ready = pyqtSignal(list)

    def __init__(self, controller_instance):
        super().__init__()
        self.controller = controller_instance

    def run(self):
        """Hàm này chỉ tải dữ liệu và phát tín hiệu."""
        try:
            print("[WorkerThread] Bắt đầu tải stats...")
            stats = self.controller._query_stats()  # Gọi hàm truy vấn stats
            self.stats_ready.emit(stats)  # Gửi kết quả về

            print("[WorkerThread] Bắt đầu tải items...")
            items = self.controller._query_items()  # Gọi hàm truy vấn items

            # print("[WorkerThread] Đang giả lập tác vụ dài... (ngủ 2 giây)")
            # time.sleep(2)

            self.items_ready.emit(items)  # Gửi kết quả về

        except Exception as e:
            print(f"LỖI trong WorkerThread: {e}")
        finally:
            self.finished.emit()

class BaseController(ABC):
    def __init__(self, parent_view):
        self.parent = parent_view
        self.query_data = QueryData()
        self._user_context = None
        self.loading_overlay = LoadingOverlay(self.parent)

        # Giữ lại tham chiếu đến thread và worker để tránh bị xóa nhầm
        self.thread = None
        self.worker = None

    def setup_for_user(self, user_context):
        print(f"DEBUG: {self.__class__.__name__}.setup_for_user được gọi.")
        self._user_context = user_context
        if not self._user_context or 'user_id' not in self._user_context:
            print(f"LỖI trong {self.__class__.__name__}: user_context không hợp lệ.")
            return
        self.refresh_data()

    # Thêm 2 phương thức trừu tượng mới cho việc TRUY VẤN
    @abstractmethod
    def _query_stats(self):
        pass

    @abstractmethod
    def _query_items(self):
        pass

    # Thêm 2 phương thức trừu tượng mới cho việc CẬP NHẬT UI
    @abstractmethod
    def _update_stats_ui(self, stats_data):
        pass

    @abstractmethod
    def _display_items_ui(self, items_data):
        pass

    def refresh_data(self):
        print("DEBUG [MainThread]: Yêu cầu làm mới dữ liệu...")
        # 1. Hiển thị loading overlay
        self.loading_overlay.start_animation()
        # 3. Đảm bảo UI được cập nhật
        QApplication.processEvents()
        # 4. Bắt đầu thread nền (logic giữ nguyên)
        self.worker = DataWorker(self)
        self.thread = QThread()
        # self.worker = DataWorker(self)
        # self.thread = QThread()
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        # Kết nối các tín hiệu mới
        self.worker.stats_ready.connect(self._update_stats_ui)
        self.worker.items_ready.connect(self._display_items_ui)
        self.worker.finished.connect(self.on_data_loaded)

        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_data_loaded(self):
        print("[MainThread] Tải dữ liệu đã xong. Ẩn loading.")
        self.loading_overlay.stop_animation()
        # if self.thread and self.thread.isRunning():
        #     self.thread.quit()
        #     self.thread.wait()