from PyQt5 import uic
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QDialog, QGridLayout
from src.models.query_data.query_data import QueryData
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent # <-- Import các thành phần media
from PyQt5.QtCore import QUrl


class VocabCardWidget(QWidget):
    """
    Một widget tùy chỉnh đại diện cho một thẻ chủ đề.
    Nó tải toàn bộ giao diện từ một file .ui riêng biệt.
    """
    play_audio_requested = pyqtSignal(str)
    def __init__(self, word_data, parent=None):
        super().__init__(parent)
        uic.loadUi("../UI/forms/vocab_card_name.ui", self)
        # if parent:
        #     self.setStyleSheet(parent.styleSheet())

        self.word_id = word_data.get('word_id')

        # --- ĐIỀN DỮ LIỆU ---
        self.vocabulary.setText(word_data.get('word_name', 'N/A'))
        self.define.setText(word_data.get('definition_vi', 'Chưa có định nghĩa'))
        self.example.setText(word_data.get('example_en', 'Chưa có ví dụ'))

        self.audio_urls = {}
        # --- XỬ LÝ PHÁT ÂM (LOGIC MỚI) ---
        pronunciations = word_data.get('pronunciations', [])

        # Ẩn tất cả các label phiên âm trước
        self.phonetic_US.hide()
        self.region_US.hide()
        self.frame_4.hide()

        self.phonetic_UK.hide()
        self.region_UK.hide()
        self.frame_5.hide()

        us_found = False
        uk_found = False

        # Lặp qua danh sách phát âm và hiển thị chúng
        for pron in pronunciations:
            region = pron.get('region', '').upper()
            phonetic_text = pron.get('phonetic_text', '')
            audio_url = pron.get('audio_url', '')

            if not audio_url: continue

            if region == 'US':
                self.region_US.setText("US")
                self.phonetic_US.setText(phonetic_text)
                self.audio_urls['US'] = audio_url
                self.region_US.show()
                self.phonetic_US.show()
                self.frame_4.show()

            elif region == 'UK':
                self.region_UK.setText("UK")
                self.phonetic_UK.setText(phonetic_text)
                self.audio_urls['UK'] = audio_url
                self.region_UK.show()
                self.phonetic_UK.show()
                self.frame_5.show()

        # --- KẾT NỐI TÍN HIỆU ---
        if hasattr(self, 'editBtn'):
            self.editBtn.clicked.connect(self.on_edit_clicked)
        if hasattr(self, 'deleteBtn'):
            self.deleteBtn.clicked.connect(self.on_delete_clicked)
        if hasattr(self, 'playAudioBtn_US'):
            self.playAudioBtn_US.clicked.connect(lambda: self.on_play_audio_clicked('US'))
        if hasattr(self, 'playAudioBtn_UK'):
            self.playAudioBtn_UK.clicked.connect(lambda: self.on_play_audio_clicked('UK'))

    def on_edit_clicked(self):
        print(f"Nút Edit của Word ID: {self.word_id} đã được nhấn!")

    def on_delete_clicked(self):
        print(f"Nút Delete của Word ID: {self.word_id} đã được nhấn!")

    def on_play_audio_clicked(self, region):
        print(f"Nút Play Audio của Word ID: {self.word_id} đã được nhấn!")

        """Phát tín hiệu mang theo URL âm thanh của vùng được yêu cầu."""
        url = self.audio_urls.get(region)
        if url:
            print(f"DEBUG: Yêu cầu phát âm thanh từ URL: {url}")
            self.play_audio_requested.emit(url)

class VocabController:
    def __init__(self, parent, user_context, topic_id):
        self.parent = parent
        self.query_data = QueryData()
        self._user_context = user_context
        self.topic_id = topic_id
        self.topic_label = self.parent.topic_label

        self.media_player = QMediaPlayer()
        # Kết nối tín hiệu lỗi để debug (rất hữu ích)
        self.media_player.error.connect(self.handle_media_error)

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

        print("DEBUG: VocabController.__init__ Hoàn thành.")

    def setup_for_user(self, user_context):
        print(f"DEBUG: VocabController.setup_for_user được gọi với context: {user_context}")
        self._user_context = user_context
        if not self._user_context or 'user_id' not in self._user_context:
            print("LỖI: user_context không hợp lệ hoặc thiếu user_id.")
            return

        self.update_stats_for_this_topic()
        self.load_and_display_words()

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def update_stats_for_this_topic(self):
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

    def load_and_display_words(self):
        print("DEBUG: Bắt đầu hàm load_and_display_words.")
        self.clear_layout(self.word_layout)

        # SỬA LỖI 1: Gọi hàm truy vấn với đúng tham số
        user_id = self._user_context['user_id']
        words = self.query_data.get_words_in_topic(self.topic_id)
        print(f"DEBUG: Các TỪ tìm thấy của user_id: {user_id} trong topic {self.topic_id}: {words}")

        if not words:
            print("DEBUG: Không có từ nào để hiển thị trong chủ đề này.")
            # Có thể hiển thị một QLabel thông báo ở đây
            return

        # Lặp qua danh sách từ, mỗi từ là một HÀNG mới
        for index, word_data in enumerate(words):
            print(f"DEBUG: Đang tạo card cho từ: {word_data.get('word_name')}")

            word_card = VocabCardWidget(word_data, parent=self.word_container)

            word_card.play_audio_requested.connect(self.play_audio)

            # Luôn đặt widget vào CỘT 0
            # Chỉ số HÀNG (row) sẽ là chỉ số index của vòng lặp
            self.word_layout.addWidget(word_card, index, 0)

        # (Tùy chọn nhưng khuyến khích)
        # Thêm một stretch vào cuối để dồn tất cả các card lên trên
        # nếu chúng không lấp đầy toàn bộ không gian
        self.word_layout.setRowStretch(len(words), 1)

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

    # def handle_edit_vocabulary_click(self):
    #     from src.views.main_view.add_vocab_view import AddWordDialog
    #     print("DEBUG: Bắt đầu tạo AddWordDialog.")
    #
    #     self.add_word_dialog = AddWordDialog(self._user_context, parent=self.parent)
    #
    #     # Bây giờ, self.add_word_dialog đã tồn tại và bạn có thể sử dụng nó
    #     self.add_word_dialog.finished.connect(self.on_add_word_dialog_finished)
    #     self.add_word_dialog.open()
    #
    #     print("DEBUG: AddWordDialog.open() đã được gọi.")
    #
    # def on_add_word_dialog_finished(self, result):
    #     """
    #     Hàm này sẽ được tự động gọi khi dialog được đóng.
    #     Tham số 'result' sẽ là QDialog.Accepted hoặc QDialog.Rejected.
    #     """
    #     print(f"DEBUG: Dialog đã đóng với kết quả: {result}")
    #     if result == QDialog.Accepted:
    #         print("DEBUG: Người dùng đã lưu từ mới. Đang làm mới giao diện...")
    #         self.update_stats_display()
    #         self.load_and_display_topics()
    #     else:
    #         print("DEBUG: Người dùng đã hủy việc thêm từ mới.")
    #
    #     # Dọn dẹp tham chiếu để cho phép Python xóa dialog khỏi bộ nhớ
    #     try:
    #         # Dùng try-except để an toàn hơn
    #         self.add_word_dialog.deleteLater()
    #         self.add_word_dialog = None
    #     except AttributeError:
    #         pass  # Bỏ qua nếu thuộc tính không còn tồn tại
