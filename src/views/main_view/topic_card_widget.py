from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget

class TopicCardWidget(QWidget):
    """
    Một widget tùy chỉnh đại diện cho một thẻ chủ đề.
    Nó tải toàn bộ giao diện từ một file .ui riêng biệt.
    """
    details_requested = pyqtSignal(int)
    def __init__(self, topic_data, parent=None):
        super().__init__(parent)
        # --- BƯỚC 1: Tải toàn bộ giao diện từ file .ui ---
        uic.loadUi("UI/forms/topic_card_name.ui", self)
        # Lưu lại topic_id
        self.topic_id = topic_data.get('topic_id')

        # --- BƯỚC 2: Tìm các widget con và điền dữ liệu ---
        # Các widget con bây giờ đã là thuộc tính của self (ví dụ: self.topic_name)
        topic_name = topic_data.get('topic_name', 'N/A')
        self.topic_name.setText(topic_name)
        word_count = topic_data.get('word_count', 0)
        self.total_word.setText(f"Số từ: {word_count}")
        # --- BƯỚC 3: Kết nối tín hiệu cho nút ---
        self.detailBtn.clicked.connect(self.on_details_clicked)

    def on_details_clicked(self):
        print(f"Nút Details của Topic ID: {self.topic_id} đã được nhấn!")
        self.details_requested.emit(self.topic_id)