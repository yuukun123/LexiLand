from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget

class VocabCardWidget(QWidget):
    """
    Một widget tùy chỉnh đại diện cho một thẻ chủ đề.
    Nó tải toàn bộ giao diện từ một file .ui riêng biệt.
    """
    play_audio_requested = pyqtSignal(str)
    edit_requested = pyqtSignal(int)
    delete_requested = pyqtSignal(int)

    def __init__(self, word_data, parent=None):
        super().__init__(parent)
        uic.loadUi("UI/forms/vocab_card_name.ui", self)
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
        self.frame_3.hide()

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
                # self.region_UK.show()
                # self.phonetic_UK.show()
                # self.frame_5.show()

        if hasattr(self, 'deleteBtn'):
            self.deleteBtn.clicked.connect(self.on_delete_clicked)
        if hasattr(self, 'playAudioBtn_US'):
            self.playAudioBtn_US.clicked.connect(lambda: self.on_play_audio_clicked('US'))
        if hasattr(self, 'playAudioBtn_UK'):
            self.playAudioBtn_UK.clicked.connect(lambda: self.on_play_audio_clicked('UK'))

    def on_delete_clicked(self):
        print(f"--- BƯỚC 1: on_delete_clicked được gọi cho word_id: {self.word_id} ---")
        self.delete_requested.emit(self.word_id)
        print(f"--- BƯỚC 2: Tín hiệu delete_requested đã được phát đi. ---")

    def on_play_audio_clicked(self, region):
        print(f"Nút Play Audio của Word ID: {self.word_id} đã được nhấn!")

        """Phát tín hiệu mang theo URL âm thanh của vùng được yêu cầu."""
        url = self.audio_urls.get(region)
        if url:
            print(f"DEBUG: Yêu cầu phát âm thanh từ URL: {url}")
            self.play_audio_requested.emit(url)