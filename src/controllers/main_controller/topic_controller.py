from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGridLayout, QWidget
from src.models.query_data.query_data import QueryData

class TopicCardWidget(QWidget):
    """
    Một widget tùy chỉnh đại diện cho một thẻ chủ đề.
    Nó tải toàn bộ giao diện từ một file .ui riêng biệt.
    """
    def __init__(self, topic_data, parent=None):
        super().__init__(parent)
        # --- BƯỚC 1: Tải toàn bộ giao diện từ file .ui ---
        uic.loadUi("../UI/forms/topic_card.ui", self)
        # Lưu lại topic_id
        self.topic_id = topic_data['topic_id']
        # --- BƯỚC 2: Tìm các widget con và điền dữ liệu ---
        # Các widget con bây giờ đã là thuộc tính của self (ví dụ: self.topic_name)
        self.topic_name.setText(topic_data['topic_name'])
        word_count = topic_data.get('word_count', 0)
        self.total_word.setText(f"Số từ: {word_count}")
        # --- BƯỚC 3: Kết nối tín hiệu cho nút ---
        self.detailBtn.clicked.connect(self.on_details_clicked)

    def on_details_clicked(self):
        print(f"Nút Details của Topic ID: {self.topic_id} đã được nhấn!")
        # (Nâng cao) Bạn có thể phát ra một tín hiệu tùy chỉnh ở đây
        # self.details_requested.emit(self.topic_id)

class VocabController:
    def __init__(self, parent_view):
        print("DEBUG: VocabController.__init__ Bắt đầu.")
        self.parent = parent_view
        self.query_data = QueryData()
        self._user_context = None

        # --- Setup UI ---
        self.topic_container = self.parent.container
        print(f"DEBUG: Container được chọn là: {self.topic_container.objectName()}")

        # Tạo và áp dụng layout cho container
        if self.topic_container.layout() is None:
            self.topic_layout = QGridLayout(self.topic_container)
        else:
            self.topic_layout = self.topic_container.layout()

        self.topic_layout.setHorizontalSpacing(15)
        self.topic_layout.setVerticalSpacing(15)

        self.topic_layout.setAlignment(Qt.AlignTop)

        print("DEBUG: VocabController.__init__ Hoàn thành.")

    def setup_for_user(self, user_context):
        print(f"DEBUG: VocabController.setup_for_user được gọi với context: {user_context}")
        self._user_context = user_context
        if not self._user_context or 'user_id' not in self._user_context:
            print("LỖI: user_context không hợp lệ hoặc thiếu user_id.")
            return

        self.load_and_display_topics()

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def load_and_display_topics(self):
        print("DEBUG: Bắt đầu hàm load_and_display_topics.")
        self.clear_layout(self.topic_layout)

        user_id = self._user_context['user_id']
        print(f"DEBUG: Đang tải topics cho user_id: {user_id}")

        topics = self.query_data.get_all_topics_with_word_count(user_id)
        print(f"DEBUG: Các topics tìm thấy từ CSDL: {topics}")

        if not topics:
            print("DEBUG: Không có topic nào để hiển thị. Dừng lại.")
            return

        num_columns = 4
        for index, topic_data in enumerate(topics):
            print(f"DEBUG: Đang tạo card cho topic: {topic_data['topic_name']}")
            topic_card = TopicCardWidget(topic_data, parent=self.topic_container)
            row = index // num_columns
            col = index % num_columns
            self.topic_layout.addWidget(topic_card, row, col)