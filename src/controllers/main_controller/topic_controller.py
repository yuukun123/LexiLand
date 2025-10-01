from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QGridLayout, QDialog, QApplication

from src.controllers.base_controller import BaseController
from src.views.main_view.topic_card_widget import TopicCardWidget

class TopicController(BaseController):
    def __init__(self, parent_view, main_window):
        # Gọi __init__ của lớp cha
        super().__init__(parent_view)
        print("DEBUG: TopicController.__init__ Bắt đầu.")
        # self.parent = parent_view
        # self.OTP = QueryData()
        # self._user_context = None
        self.main_window_ref = main_window

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

        self.items_layout = self.topic_layout

        print("DEBUG: TopicController.__init__ Hoàn thành.")

    def _query_stats(self):
        """Hàm này chỉ truy vấn CSDL, không đụng đến UI."""
        return self.query_data.get_user_stats(self._user_context['user_id'])

    def _query_items(self):
        """Hàm này chỉ truy vấn CSDL, không đụng đến UI."""
        return self.query_data.get_all_topics_with_word_count(self._user_context['user_id'])

    def _update_stats_ui(self, stats):
        """Hàm này chỉ cập nhật UI, không truy vấn CSDL."""
        print(f"[MainThread] TopicController đang cập nhật stats UI: {stats}")
        if hasattr(self.parent, 'learned'): self.parent.learned.setText(str(stats["learned"]))
        if hasattr(self.parent, 'memorized'): self.parent.memorized.setText(str(stats["memorized"]))
        if hasattr(self.parent, 'review'): self.parent.review.setText(str(stats["review_needed"]))

    # def load_and_display_topics(self):
    #     print("DEBUG: Bắt đầu hàm load_and_display_topics.")
    #     self.clear_layout(self.topic_layout)
    #
    #     user_id = self._user_context['user_id']
    #     # self.OTP.debug_user_data(user_id)
    #     print(f"DEBUG: Đang tải topics cho user_id: {user_id}")
    #     topics = self.OTP.get_all_topics_with_word_count(user_id)
    #     print(f"DEBUG: Các topics tìm thấy từ CSDL: {topics}")
    #
    #     if not topics:
    #         print("DEBUG: Không có topic nào để hiển thị. Dừng lại.")
    #         return
    #
    #     num_columns = 4
    #     for index, topic_data in enumerate(topics):
    #         print(f"DEBUG: Đang tạo card cho topic: {topic_data['topic_name']}")
    #         topic_card = TopicCardWidget(topic_data, parent=self.topic_container)
    #         topic_card.details_requested.connect(self.handle_details_requested)
    #         row = index // num_columns
    #         col = index % num_columns
    #         self.topic_layout.addWidget(topic_card, row, col)

    def _display_items_ui(self, topics):
        """Hàm này chỉ cập nhật UI, không truy vấn CSDL."""
        print(f"[MainThread] TopicController đang hiển thị {len(topics)} topics...")
        # Xóa layout cũ
        while self.topic_layout.count():
            child = self.topic_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()

        if not topics: return

        # Tạo và thêm card (thao tác GUI)
        num_columns = 4
        for index, topic_data in enumerate(topics):
            topic_card = TopicCardWidget(topic_data, parent=self.topic_container)
            topic_card.details_requested.connect(self.handle_details_requested)
            row = index // num_columns
            col = index % num_columns
            self.topic_layout.addWidget(topic_card, row, col)

    def handle_add_vocabulary_click(self):
        """
        Xử lý khi người dùng nhấn nút "+ Add vocabulary".
        Hiển thị loading TRƯỚC KHI tạo dialog.
        """
        print("DEBUG: Yêu cầu mở AddWordDialog. Hiển thị loading...")

        # 1. HIỂN THỊ LOADING NGAY LẬP TỨC TRÊN TOPICWINDOW
        self.loading_overlay.start_animation()
        QApplication.processEvents()  # Ép UI vẽ lại ngay

        # 2. DÙNG QTIMER ĐỂ TRÌ HOÃN VIỆC TẠO DIALOG
        # Cho phép loading có thời gian hiển thị mượt mà
        QTimer.singleShot(50, self._create_and_prepare_add_dialog)

    def _create_and_prepare_add_dialog(self):
        """
        Hàm này tạo dialog và bắt đầu quá trình tải dữ liệu nền của nó.
        Nó chạy sau một khoảng trễ nhỏ.
        """
        from src.views.main_view.add_vocab_view import AddWordDialog

        print("DEBUG: Đang tạo AddWordDialog ở nền...")

        # Tạo dialog, nó sẽ tự tạo controller của nó
        self.add_word_dialog = AddWordDialog(self._user_context, parent=self.parent)

        # Kết nối tín hiệu "ready_to_show" của dialog với hàm của chúng ta
        self.add_word_dialog.ready_to_show.connect(self._on_add_dialog_ready)

        # Kết nối tín hiệu "finished" để làm mới dữ liệu
        self.add_word_dialog.finished.connect(self.on_add_word_dialog_finished)

        # Bắt đầu quá trình tải dữ liệu nền BÊN TRONG dialog
        # Dòng này sẽ kích hoạt loading (nếu có) BÊN TRONG dialog
        self.add_word_dialog.controller.load_initial_data()

    def _on_add_dialog_ready(self):
        """
        Slot được gọi khi AddWordDialog đã tải xong topics và sẵn sàng.
        """
        print("DEBUG: AddWordDialog đã sẵn sàng. Ẩn loading và hiển thị dialog.")

        # ẨN LOADING TRÊN TOPICWINDOW
        self.loading_overlay.stop_animation()

        # HIỂN THỊ DIALOG
        # Dùng .open() thay vì .exec_() để tránh blocking nếu dialog có tác vụ async
        self.add_word_dialog.open()

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
            self.vocab_window.data_changed.connect(self.refresh_data)
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

            self.refresh_data()
        else:
            print("DEBUG: Người dùng đã hủy việc thêm từ mới.")

        # Dọn dẹp tham chiếu để cho phép Python xóa dialog khỏi bộ nhớ
        try:
            # Dùng try-except để an toàn hơn
            self.add_word_dialog.deleteLater()
            self.add_word_dialog = None
        except AttributeError:
            pass  # Bỏ qua nếu thuộc tính không còn tồn tại