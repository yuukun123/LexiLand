from PyQt5 import uic
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QGridLayout, QWidget, QDialog
from src.models.query_data.query_data import QueryData


class TopicCardWidget(QWidget):
    """
    Một widget tùy chỉnh đại diện cho một thẻ chủ đề.
    Nó tải toàn bộ giao diện từ một file .ui riêng biệt.
    """
    details_requested = pyqtSignal(int)
    def __init__(self, topic_data, parent=None):
        super().__init__(parent)
        # --- BƯỚC 1: Tải toàn bộ giao diện từ file .ui ---
        uic.loadUi("../UI/forms/topic_card_name.ui", self)
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


class TopicController:
    def __init__(self, parent, main_window):
        print("DEBUG: TopicController.__init__ Bắt đầu.")
        self.parent = parent
        self.query_data = QueryData()
        self._user_context = None
        self.main_window_ref = main_window
        # self.vocab_window = None

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

        print("DEBUG: TopicController.__init__ Hoàn thành.")

    def setup_for_user(self, user_context):
        print(f"DEBUG: TopicController.setup_for_user được gọi với context: {user_context}")
        self._user_context = user_context
        if not self._user_context or 'user_id' not in self._user_context:
            print("LỖI: user_context không hợp lệ hoặc thiếu user_id.")
            return

        self.update_stats_display()
        self.load_and_display_topics()

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def update_stats_display(self):
        if not self._user_context or 'user_id' not in self._user_context:
            print("LỖI: user_context không hợp lệ hoặc thiếu user_id.")
            return

        user_id = self._user_context['user_id']
        stats = self.query_data.get_user_stats(user_id)
        print(f"DEBUG: Cập nhật thông tin user_id: {user_id}")

        if hasattr(self.parent, 'learned'):
            self.parent.learned.setText(str(stats["learned"]))

        # Ví dụ, nếu widget hiển thị số 50 (Đã nhớ) có objectName là 'memorizedCountLabel'
        if hasattr(self.parent, 'memorized'):
            self.parent.memorized.setText(str(stats["memorized"]))

        # Ví dụ, nếu widget hiển thị số 50 (Cần ôn tập) có objectName là 'reviewCountLabel'
        if hasattr(self.parent, 'review'):
            self.parent.review.setText(str(stats["review_needed"]))

    def load_and_display_topics(self):
        print("DEBUG: Bắt đầu hàm load_and_display_topics.")
        self.clear_layout(self.topic_layout)

        user_id = self._user_context['user_id']
        self.query_data.debug_user_data(user_id)
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
            topic_card.details_requested.connect(self.handle_details_requested)
            row = index // num_columns
            col = index % num_columns
            self.topic_layout.addWidget(topic_card, row, col)

    def handle_add_vocabulary_click(self):
        from src.views.main_view.add_vocab_view import AddWordDialog
        print("DEBUG: Bắt đầu tạo AddWordDialog.")

        self.add_word_dialog = AddWordDialog(self._user_context, parent=self.parent)

        # Bây giờ, self.add_word_dialog đã tồn tại và bạn có thể sử dụng nó
        self.add_word_dialog.finished.connect(self.on_add_word_dialog_finished)
        self.add_word_dialog.open()

        print("DEBUG: AddWordDialog.open() đã được gọi.")

    def handle_details_requested(self, topic_id):
        """
        Đây là KHE (SLOT). Hàm này được gọi khi bất kỳ TopicCardWidget nào
        phát ra tín hiệu 'details_requested'.
        """
        print(f"DEBUG: TopicController đã nhận được yêu cầu xem chi tiết cho topic_id: {topic_id}")

        # Controller bây giờ có đầy đủ thông tin để mở cửa sổ mới
        if not self._user_context:
            return

        # Import tại chỗ để tránh circular import
        # from src.views.main_view.vocab_view import VocabWindow
        from src.windows.window_manage import open_vocab_window

        try:
            topic_window = self.parent
            self.parent.hide()

            # Tạo và hiển thị cửa sổ chi tiết
            # Cửa sổ này sẽ cần user_context và topic_id để truy vấn CSDL
            current_username = self._user_context.get('user_name')
            self.vocab_window = open_vocab_window(
                current_username,
                topic_id,
                pre_window = topic_window,
                parent = topic_window
            )
            self.vocab_window.vocab_controller.setup_for_user(self._user_context)

            # Ẩn cửa sổ hiện tại và hiển thị cửa sổ mới
            # self.vocab_window.show()

        except Exception as e:
            print(f"LỖI khi mở cửa sổ chi tiết: {e}")
            import traceback
            traceback.print_exc()
            self.parent.show()

    def on_add_word_dialog_finished(self, result):
        """
        Hàm này sẽ được tự động gọi khi dialog được đóng.
        Tham số 'result' sẽ là QDialog.Accepted hoặc QDialog.Rejected.
        """
        print(f"DEBUG: Dialog đã đóng với kết quả: {result}")
        if result == QDialog.Accepted:
            print("DEBUG: Người dùng đã lưu từ mới. Đang làm mới giao diện...")
            self.update_stats_display()
            self.load_and_display_topics()
        else:
            print("DEBUG: Người dùng đã hủy việc thêm từ mới.")

        # Dọn dẹp tham chiếu để cho phép Python xóa dialog khỏi bộ nhớ
        try:
            # Dùng try-except để an toàn hơn
            self.add_word_dialog.deleteLater()
            self.add_word_dialog = None
        except AttributeError:
            pass  # Bỏ qua nếu thuộc tính không còn tồn tại