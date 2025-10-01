from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QDialog, QGridLayout, QMessageBox, QApplication

from src.controllers.base_controller import BaseController
from src.services.query_data.query_data import QueryData
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent # <-- Import các thành phần media
from PyQt5.QtCore import QUrl
from src.views.main_view.practice_view  import PracticeWindow
from src.views.main_view.vocab_card_widget import VocabCardWidget

class VocabController(BaseController):
    def __init__(self, parent_view, user_context, topic_id):
        # Gọi __init__ của lớp cha
        super().__init__(parent_view)
        self.parent = parent_view
        self.query_data = QueryData()
        self._user_context = user_context
        self.topic_id = topic_id

        self.topic_id_list = []
        self.topic_id_list.append(topic_id)
        self.topic_label = self.parent.topic_label

        self.topic_label = self.parent.topic_label
        self.media_player = QMediaPlayer()
        self.media_player.error.connect(self.handle_media_error)
        if hasattr(self.parent, 'Add_word_btn'):
            self.parent.Add_word_btn.clicked.connect(self.handle_add_word_click)

        # --- Setup UI ---
        self.word_container = self.parent.word_container
        print(f"DEBUG: Container được chọn là: {self.word_container.objectName()}")
        # Tạo và áp dụng layout cho container
        if self.word_container.layout() is None:
            self.word_layout = QGridLayout(self.word_container)
        else:
            self.word_layout = self.word_container.layout()

        self.word_layout.setSpacing(15)
        self.word_layout.setAlignment(Qt.AlignTop)

        self.items_layout = self.word_layout

        print("DEBUG: VocabController.__init__ Hoàn thành.")

    def __del__(self):
        print(f"!!! CẢNH BÁO: Controller tại địa chỉ {id(self)} đang bị hủy (garbage collected) !!!")

    def _query_stats(self):
        return self.query_data.get_stats_for_topic(self._user_context['user_id'], self.topic_id)

    def _query_items(self):
        return self.query_data.get_words_in_topic(self.topic_id)

    def _update_stats_ui(self, stats):
        if not self._user_context or 'user_id' not in self._user_context:
            print("LỖI: user_context không hợp lệ hoặc thiếu user_id.")
            return

        user_id = self._user_context['user_id']
        stats = self.query_data.get_stats_for_topic(user_id, self.topic_id)
        print(f"DEBUG: Cập nhật thông tin user_id: {user_id}, topic_id: {self.topic_id}")

        topic_name = self.query_data.get_topic_name_from_topic_id(user_id, self.topic_id)
        self.topic_label.setText(f"Topic: {topic_name}")

        if hasattr(self.parent, 'learned'):
            self.parent.learned.setText(str(stats["learned"]))
        if hasattr(self.parent, 'memorized'):
            self.parent.memorized.setText(str(stats["memorized"]))
        if hasattr(self.parent, 'review'):
            self.parent.review.setText(str(stats["review_needed"]))

    def _display_items_ui(self, words):
        print("DEBUG: Bắt đầu hàm load_and_display_words.")
        # self.clear_layout(self.word_layout)

        # SỬA LỖI 1: Gọi hàm truy vấn với đúng tham số
        # user_id = self._user_context['user_id']
        # words = self.OTP.get_words_in_topic(self.topic_id)
        # print(f"DEBUG: Các TỪ tìm thấy của user_id: {user_id} trong topic {self.topic_id}: {words}")
        # --- THÊM LẠI LOGIC XÓA VÀO ĐÂY ---

        while self.items_layout.count():
            child = self.items_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not words:
            print("DEBUG: Không có từ nào để hiển thị trong chủ đề này.")
            # Có thể hiển thị một QLabel thông báo ở đây
            return

        # Lặp qua danh sách từ, mỗi từ là một HÀNG mới
        for index, word_data in enumerate(words):
            print(f"DEBUG: Đang tạo card cho từ: {word_data.get('word_name')}")

            word_card = VocabCardWidget(word_data, parent=self.word_container)

            word_card.play_audio_requested.connect(self.play_audio)
            # word_card.edit_requested.connect(self.handle_edit_word_click)
            word_card.delete_requested.connect(self.handle_delete_word_click)
            print(f"DEBUG: Đã kết nối delete_requested của card '{word_data.get('word_name')}' vào slot tại địa chỉ: {id(self.handle_delete_word_click)}")

            # print(f"DEBUG: Đã kết nối tín hiệu 'edit_requested' cho word '{word_data.get('word_name')}' vào {self.handle_edit_word_click}")

            # Luôn đặt widget vào CỘT 0
            # Chỉ số HÀNG (row) sẽ là chỉ số index của vòng lặp
            self.word_layout.addWidget(word_card, index, 0)

        self.word_layout.setRowStretch(len(words), 1)

    # def setup_for_user(self, user_context):
    #     print(f"DEBUG: VocabController.setup_for_user được gọi với context: {user_context}")
    #     self._user_context = user_context
    #     if not self._user_context or 'user_id' not in self._user_context:
    #         print("LỖI: user_context không hợp lệ hoặc thiếu user_id.")
    #         return
    #
    #     self.update_stats_for_this_topic()
    #     self.load_and_display_words()

    # def clear_layout(self, layout):
    #     while layout.count():
    #         child = layout.takeAt(0)
    #         if child.widget():
    #             child.widget().deleteLater()

    # def update_stats_for_this_topic(self):
    #     if not self._user_context or 'user_id' not in self._user_context:
    #         print("LỖI: user_context không hợp lệ hoặc thiếu user_id.")
    #         return
    #
    #     user_id = self._user_context['user_id']
    #     stats = self.OTP.get_stats_for_topic(user_id, self.topic_id)
    #     print(f"DEBUG: Cập nhật thông tin user_id: {user_id}, topic_id: {self.topic_id}")
    #
    #     topic_name = self.OTP.get_topic_name_from_topic_id(user_id, self.topic_id)
    #     self.topic_label.setText(f"Topic: {topic_name}")
    #
    #     if hasattr(self.parent, 'learned'):
    #         self.parent.learned.setText(str(stats["learned"]))
    #     if hasattr(self.parent, 'memorized'):
    #         self.parent.memorized.setText(str(stats["memorized"]))
    #     if hasattr(self.parent, 'review'):
    #         self.parent.review.setText(str(stats["review_needed"]))

    # def load_and_display_words(self):
    #     print("DEBUG: Bắt đầu hàm load_and_display_words.")
    #     self.clear_layout(self.word_layout)
    #
    #     # SỬA LỖI 1: Gọi hàm truy vấn với đúng tham số
    #     user_id = self._user_context['user_id']
    #     words = self.OTP.get_words_in_topic(self.topic_id)
    #     print(f"DEBUG: Các TỪ tìm thấy của user_id: {user_id} trong topic {self.topic_id}: {words}")
    #
    #     if not words:
    #         print("DEBUG: Không có từ nào để hiển thị trong chủ đề này.")
    #         # Có thể hiển thị một QLabel thông báo ở đây
    #         return
    #
    #     # Lặp qua danh sách từ, mỗi từ là một HÀNG mới
    #     for index, word_data in enumerate(words):
    #         print(f"DEBUG: Đang tạo card cho từ: {word_data.get('word_name')}")
    #
    #         word_card = VocabCardWidget(word_data, parent=self.word_container)
    #
    #         word_card.play_audio_requested.connect(self.play_audio)
    #         # word_card.edit_requested.connect(self.handle_edit_word_click)
    #         word_card.delete_requested.connect(self.handle_delete_word_click)
    #         print(f"DEBUG: Đã kết nối delete_requested của card '{word_data.get('word_name')}' vào slot tại địa chỉ: {id(self.handle_delete_word_click)}")
    #
    #         # print(f"DEBUG: Đã kết nối tín hiệu 'edit_requested' cho word '{word_data.get('word_name')}' vào {self.handle_edit_word_click}")
    #
    #         # Luôn đặt widget vào CỘT 0
    #         # Chỉ số HÀNG (row) sẽ là chỉ số index của vòng lặp
    #         self.word_layout.addWidget(word_card, index, 0)
    #
    #     self.word_layout.setRowStretch(len(words), 1)

    def play_audio(self, audio_url):
        """Slot này nhận URL và ra lệnh cho media player phát nhạc."""
        if not audio_url:
            print("CẢNH BÁO: URL âm thanh rỗng, không thể phát.")
            return

        # Kiểm tra xem URL là link web hay file cục bộ
        if audio_url.startswith("http"):
            url = QUrl(audio_url)
        else:
            # Nếu là đường dẫn file cục bộ
            url = QUrl.fromLocalFile(audio_url)

        print(f"DEBUG: Đang chuẩn bị phát từ QUrl: {url.toString()}")
        content = QMediaContent(url)
        self.media_player.setMedia(content)
        self.media_player.play()

    def handle_media_error(self):
        """Hàm này sẽ được gọi nếu QMediaPlayer gặp lỗi."""
        print(f"LỖI MEDIA PLAYER: {self.media_player.errorString()}")

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

    def handle_add_word_click(self):
        """Bắt đầu quá trình mở dialog với hiệu ứng loading."""
        print("DEBUG: Yêu cầu mở AddWordDialog. Hiển thị loading...")
        self.loading_overlay.start_animation()
        QApplication.processEvents()

        # Trì hoãn việc tạo dialog
        QTimer.singleShot(50, self._create_and_prepare_add_dialog)

    def _create_and_prepare_add_dialog(self):
        """Tạo và chuẩn bị dialog ở nền."""
        from src.views.main_view.add_vocab_view import AddWordDialog

        self.add_word_dialog = AddWordDialog(
            user_context=self._user_context,
            parent=self.parent,
            mode="add"
        )

        # Kết nối các tín hiệu
        self.add_word_dialog.ready_to_show.connect(self._on_add_dialog_ready)
        self.add_word_dialog.finished.connect(self._on_add_dialog_finished)

        # Tự động chọn topic và bắt đầu tải dữ liệu nền của dialog
        self._prepare_dialog_for_current_topic()
        self.add_word_dialog.controller.load_initial_data()

    def _prepare_dialog_for_current_topic(self):
        """Hàm helper để thiết lập topic cho dialog."""
        try:
            index = self.add_word_dialog.controller.view.Topic_opt.findData(self.topic_id)
            if index >= 0:
                # Chỉ cần gọi hàm này một lần, on_topics_loaded sẽ xử lý
                pass
        except Exception as e:
            print(f"Lỗi khi chuẩn bị dialog: {e}")

    def _on_add_dialog_ready(self):
        """Được gọi khi dialog đã sẵn sàng để hiển thị."""
        print("DEBUG: Dialog đã sẵn sàng. Ẩn loading và hiển thị dialog.")

        # Tự động chọn topic hiện tại sau khi combobox đã được điền
        index = self.add_word_dialog.controller.view.Topic_opt.findData(self.topic_id)
        if index >= 0:
            self.add_word_dialog.controller.view.Topic_opt.setCurrentIndex(index)
            self.add_word_dialog.controller.view.Topic_opt.setEnabled(False)
            self.add_word_dialog.controller.view.addTopicLabel.hide()
            self.add_word_dialog.controller.view.topic_input.hide()

        self.loading_overlay.stop_animation()
        self.add_word_dialog.open()

    def _on_add_dialog_finished(self, result):
        """Được gọi khi dialog đóng lại."""
        if result == QDialog.Accepted:
            self.refresh_data()
            self.parent.data_changed.emit()

        # Dọn dẹp
        self.add_word_dialog.deleteLater()
        self.add_word_dialog = None

    def handle_delete_word_click(self, word_id):
        """
        Xử lý khi người dùng yêu cầu xóa một từ khỏi chủ đề hiện tại.
        """
        print(f"DEBUG: Controller đã nhận yêu cầu xóa word_id: {word_id}")

        # Lấy tên từ để hiển thị trong hộp thoại xác nhận
        word_details = self.query_data.get_full_word_details(word_id)
        word_name = word_details.get('word_name', 'từ này') if word_details else 'từ này'

        # 1. Hiển thị hộp thoại xác nhận
        reply = QMessageBox.question(
            self.parent,
            'Xác nhận xóa',
            f"Bạn có chắc chắn muốn xóa từ '{word_name}' khỏi chủ đề này không?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No  # Nút mặc định là No
        )

        # 2. Xử lý câu trả lời của người dùng
        if reply == QMessageBox.Yes:
            print(f"DEBUG: Người dùng đã xác nhận xóa word_id: {word_id}")

            # 3. Gọi hàm CSDL để xóa
            result = self.query_data.remove_word_from_topic(self.topic_id, word_id)

            if result.get("success"):
                QMessageBox.information(self.parent, "Thành công", f"Đã xóa từ '{word_name}'.")
                # 4. Làm mới giao diện
                self.refresh_data()

                self.parent.data_changed.emit()

        # if reply == QMessageBox.Yes:
        #     # Gọi hàm CSDL để xóa
        #     result = self.OTP.remove_word_from_topic(self.topic_id, word_id)
        #
        #     if result.get("success"):
        #         QMessageBox.information(self.parent, "Thành công", f"Đã xóa từ '{word_name}'.")
        #
        #         # --- BƯỚC MỚI: XỬ LÝ XÓA FILE ---
        #         files_to_delete = result.get("deleted_audio_files", [])
        #         if files_to_delete:
        #             self.cleanup_audio_files(files_to_delete)
        #
        #         # Làm mới giao diện
        #         self.refresh_data()
        #         self.parent.data_changed.emit()

            else:
                QMessageBox.critical(self.parent, "Lỗi", f"Không thể xóa từ: {result.get('error')}")
        else:
            print("DEBUG: Người dùng đã hủy việc xóa.")

    # def cleanup_audio_files(self, file_paths):
    #     """
    #     Xóa các file âm thanh không còn cần thiết khỏi hệ thống file.
    #     """
    #     print(f"DEBUG: Bắt đầu dọn dẹp các file audio: {file_paths}")
    #     for path in file_paths:
    #         if path and os.path.exists(path):
    #             try:
    #                 os.remove(path)
    #                 print(f"INFO: Đã xóa file: {path}")
    #             except OSError as e:
    #                 print(f"LỖI: Không thể xóa file {path}: {e}")
    #         else:
    #             print(f"CẢNH BÁO: Đường dẫn file không hợp lệ hoặc không tồn tại: {path}")

    def handle_open_practice_click(self):
        print("DEBUG: start open_practice_window")
        if not self._user_context:
            # Sử dụng self._user_context để lấy username cho thông báo lỗi
            user_name_for_msg = self.username # Hoặc một giá trị mặc định
            QMessageBox.critical(self, "Lỗi nghiêm trọng", f"Không thể tìm thấy dữ liệu cho người dùng '{user_name_for_msg}'.")
            return
        try:
            self.parent.hide()
            current_username = self._user_context.get('user_name')
            user_id = self._user_context.get('user_id')
            topics = self.query_data.get_name_topic_by_id(user_id, self.topic_id_list)
            self.practice_window = PracticeWindow(user_context = self._user_context, topics = topics, parent=self.parent)
            self.practice_window.practice_controller.setup_for_user(self._user_context)
            print("DEBUG: practice_window created", self.practice_window)
            self.practice_window.show()
            print("DEBUG: practice_window show called")
        except Exception as e:
            print("ERROR while opening topic window:", e)
            self.parent.show()

