# trong src/controllers/main_controller/add_word_controller.py
import asyncio

from PyQt5.QtWidgets import QMessageBox
import aiohttp

from src.models.query_data.query_data import QueryData
from src.models.API.word_api import run_lookup, lookup_and_build_data # Giả sử bạn có hàm này


class AddWordController:
    def __init__(self, view, user_context, mode, topic_data=None):
        self.view = view  # view ở đây là AddWordDialog
        self._user_context = user_context
        self.mode = mode
        self.topic_data_on_edit = topic_data  # Dữ liệu gốc khi edit
        self.query_data = QueryData()

        # Kết nối các nút của dialog
        self.view.SaveVocabBtn.clicked.connect(self.handle_save)
        self.view.CreateVocabBtn.clicked.connect(self.handle_create_definition_wrapper)

        # Tải danh sách topics vào ComboBox
        self.load_topics_into_combobox()

    def load_topics_into_combobox(self):
        user_id = self._user_context['user_id']
        topics = self.query_data.get_all_topics_with_word_count(user_id)  # Cần hàm này

        # Xóa các item cũ
        self.view.Topic_opt.clear()

        # Thêm các topic vào combobox
        for topic in topics:
            self.view.Topic_opt.addItem(topic['topic_name'], topic['topic_id'])

        # Nếu là chế độ edit, chọn topic hiện tại
        if self.mode == "edit" and self.topic_data_on_edit:
            topic_id = self.topic_data_on_edit.get('topic_id')
            index = self.view.Topic_opt.findData(topic_id)
            if index >= 0:
                self.view.Topic_opt.setCurrentIndex(index)

    def handle_create_definition_wrapper(self):
        word = self.view.vocab.text().strip()
        if not word:
            QMessageBox.warning(self.view, "Warning", "Please enter an English word first.")
            return

        self.view.definition.setText("Searching for definition...")
        self.view.example.setText("Searching for example...")

        task = asyncio.create_task(self.lookup_word_async(word))
        task.add_done_callback(self.on_lookup_finished)

    async def lookup_word_async(self, word):
        try:
            async with aiohttp.ClientSession() as session:
                word_info = await lookup_and_build_data(session, word)
                return word_info
        except Exception as e:
            print(f"Lỗi khi gọi API: {e}")
            return None

    def on_lookup_finished(self, task):
        try:
            word_info = task.result()

            self.view.retrieved_word_data = word_info

            if word_info and word_info.get('meanings'):
                meaning = word_info['meanings'][0]

                definition_text = meaning.get('definition_vi', 'Could not find definition.')
                example_text = meaning.get('example_en', 'Could not find example.')

                self.view.definition.setText(definition_text)
                self.view.example.setText(example_text)
            else:
                self.view.definition.setText("Could not find definition.")
                self.view.example.setText("Could not find example.")
        except Exception as e:
            print(f"Lỗi khi gọi API: {e}")
            self.view.definition.setText(f"Error: {e}")

    def handle_save(self):
        # 1. Kiểm tra xem đã có dữ liệu từ API chưa
        if not hasattr(self.view, 'retrieved_word_data') or not self.view.retrieved_word_data:
            QMessageBox.warning(self.view, "Thiếu thông tin", "Vui lòng nhấn 'Create Definition And Example' trước khi lưu.")
            return

        word_data_to_save = self.view.retrieved_word_data

        # 2. Xử lý Topic
        new_topic_name = self.view.topic_input.text().strip()
        target_topic_id = None

        if new_topic_name:
            # Ưu tiên tạo topic mới nếu người dùng nhập vào
            result = self.query_data.add_topic(self._user_context['user_id'], new_topic_name)
            if result['success']:
                target_topic_id = result['topic_id']
            else:
                QMessageBox.critical(self.view, "Error", f"Could not create topic: {result['error']}")
                return
        else:
            # Nếu không, lấy topic đã chọn từ combobox
            target_topic_id = self.view.Topic_opt.currentData()

        if target_topic_id is None:
            # Tự động gán vào topic "Other" nếu không chọn
            target_topic_id = self.query_data.get_other_topic_id(self._user_context['user_id'])
            if target_topic_id is None:
                QMessageBox.warning(self.view, "Lỗi", "Không tìm thấy chủ đề mặc định 'Other'.")
                return

        # 3. Gọi hàm lưu vào CSDL
        result = self.query_data.add_word_to_topic(
            target_topic_id,
            word_data_to_save,
            self._user_context['user_id']
        )

        if result["success"]:
            self.view.accept()  # Đóng dialog và báo thành công
        else:
            QMessageBox.critical(self.view, "Database Error", f"Failed to save word: {result['error']}")