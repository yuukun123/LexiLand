import asyncio
import aiohttp
from PyQt5.QtCore import QThread, QObject, pyqtSignal
from PyQt5.QtWidgets import QMessageBox, QApplication

from src.models.query_data.query_data import QueryData
from src.models.API.word_api import run_lookup, lookup_and_build_data # Giả sử bạn có hàm này

class TopicLoaderWorker(QObject):
    finished = pyqtSignal(list) # Tín hiệu mang theo danh sách topics

    def __init__(self, query_data, user_id):
        super().__init__()
        self.query_data = query_data
        self.user_id = user_id

    def run(self):
        """Chạy truy vấn CSDL ở nền."""
        print("[WorkerThread] Đang tải danh sách topics...")
        topics = self.query_data.get_all_topics_with_word_count(self.user_id)
        self.finished.emit(topics)

class AddWordController:
    def __init__(self, view, user_context, mode, word_data_to_edit=None):
        self.view = view  # view ở đây là AddWordDialog
        self._user_context = user_context
        self.mode = mode
        self.word_data_to_edit = word_data_to_edit  # Dữ liệu gốc khi edit
        self.query_data = QueryData()

        # Kết nối các nút của dialog
        self.view.CreateVocabBtn.clicked.connect(self.handle_create_definition_wrapper)
        # --- THAY ĐỔI 1: Kết nối tín hiệu của ComboBox ---
        self.view.Topic_opt.currentIndexChanged.connect(self.on_topic_selection_changed)

        # Ban đầu, ẩn ô nhập topic mới
        self.view.topic_input.hide()
        self.view.addTopicLabel.hide()

        # Tải danh sách topics vào ComboBox
        # self.load_topics_into_combobox()
        # self.populate_form_if_editing()

    def load_initial_data(self):
        # """Bắt đầu quá trình tải dữ liệu nền cho dialog."""
        # # Hiển thị loading ngay khi mở
        # self.view.loading_overlay.start_animation()
        # QApplication.processEvents()  # Đảm bảo UI được vẽ

        # Tạo và chạy thread để tải topics
        self.topic_loader_worker = TopicLoaderWorker(self.query_data, self._user_context['user_id'])
        self.topic_loader_thread = QThread()
        self.topic_loader_worker.moveToThread(self.topic_loader_thread)

        self.topic_loader_thread.started.connect(self.topic_loader_worker.run)
        self.topic_loader_worker.finished.connect(self.on_topics_loaded)

        self.topic_loader_worker.finished.connect(self.topic_loader_thread.quit)
        self.topic_loader_worker.finished.connect(self.topic_loader_worker.deleteLater)
        self.topic_loader_thread.finished.connect(self.topic_loader_thread.deleteLater)

        self.topic_loader_thread.start()

    def on_topics_loaded(self, topics):
        """Slot được gọi khi thread tải topics hoàn thành."""
        print("[MainThread] Đã tải xong topics. Đang điền vào ComboBox...")

        # --- Logic điền ComboBox (giống như hàm load_topics_into_combobox cũ) ---
        self.view.Topic_opt.blockSignals(True)
        self.view.Topic_opt.clear()
        self.view.Topic_opt.addItem("--- Choose a topic ---", None)
        self.view.Topic_opt.addItem("-- Add New Topic --", -1)
        if topics:
            self.view.Topic_opt.insertSeparator(2)
        for topic in topics:
            self.view.Topic_opt.addItem(topic['topic_name'], topic['topic_id'])
        self.view.Topic_opt.blockSignals(False)

        # Điền dữ liệu cho chế độ edit (nếu có)
        self.populate_form_if_editing()
        self.view.ready_to_show.emit()

    def populate_form_if_editing(self):
        """Điền dữ liệu có sẵn vào form nếu đang ở chế độ edit."""
        if self.mode == "edit" and self.word_data_to_edit:
            self.view.setWindowTitle("Edit Word")  # Đổi tiêu đề cửa sổ
            self.view.label.setText("Edit Word")

            # Điền các trường text
            self.view.vocab.setText(self.word_data_to_edit.get('word_name', ''))
            if self.word_data_to_edit.get('meanings'):
                first_meaning = self.word_data_to_edit['meanings'][0]
                self.view.definition.setText(first_meaning.get('definition_vi', ''))
                self.view.example.setText(first_meaning.get('example_en', ''))

                # Nút "Create..." bị vô hiệu hóa
            # self.view.CreateVocabBtn.setEnabled(False)

    def load_topics_into_combobox(self):
        user_id = self._user_context['user_id']
        topics = self.query_data.get_all_topics_with_word_count(user_id)  # Cần hàm này

        self.view.Topic_opt.blockSignals(True)

        # Xóa các item cũ
        self.view.Topic_opt.clear()

        self.view.Topic_opt.addItem("--- Choose a topic ---", None)
        self.view.Topic_opt.addItem("--Add New Topic--", -1)

        if topics:
            self.view.Topic_opt.insertSeparator(2)

        # Thêm các topic vào combobox
        for topic in topics:
            self.view.Topic_opt.addItem(topic['topic_name'], topic['topic_id'])

        self.view.Topic_opt.blockSignals(False)

        # Nếu là chế độ edit, chọn topic hiện tại
        if self.mode == "edit" and self.word_data_to_edit:
            topic_id = self.word_data_to_edit.get('topic_id')
            index = self.view.Topic_opt.findData(topic_id)
            if index >= 0:
                self.view.Topic_opt.setCurrentIndex(index)
        else:
            self.view.Topic_opt.setCurrentIndex(0)

    def on_topic_selection_changed(self, index):
        """Hàm được gọi mỗi khi người dùng thay đổi lựa chọn trong ComboBox."""
        # Lấy userData của item được chọn
        selected_data = self.view.Topic_opt.itemData(index)

        # --- THAY ĐỔI 3: Logic ẩn/hiện ---
        # Nếu userData là -1 (item "Add New Topic"), thì hiển thị ô input
        if selected_data == -1:
            self.view.topic_input.show()
            self.view.addTopicLabel.show()
        else:
            self.view.topic_input.hide()
            self.view.addTopicLabel.hide()
            self.view.topic_input.clear()  # Xóa text cũ nếu có

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
        form_data = self.view.get_form_data()

        # 1. Kiểm tra xem đã có dữ liệu từ API chưa
        if not hasattr(self.view, 'retrieved_word_data') or not self.view.retrieved_word_data:
            QMessageBox.warning(self.view, "Thiếu thông tin", "Vui lòng nhấn 'Create Definition And Example' trước khi lưu.")
            return

        # word_data_to_save = self.view.retrieved_word_data

        # 2. Xử lý Topic
        new_topic_name = self.view.topic_input.text().strip()
        target_topic_id = None

        if new_topic_name and self.view.Topic_opt.currentData():
            # Ưu tiên tạo topic mới nếu người dùng nhập vào
            print(f"Debug đang tạo topic mới: '{new_topic_name}'")
            result = self.query_data.add_topic(self._user_context['user_id'], new_topic_name)

            if result['success']:
                target_topic_id = result['topic_id']
                self.load_topics_into_combobox()
                index = self.view.Topic_opt.findData(target_topic_id)
                if index > 0:
                    self.view.Topic_opt.setCurrentIndex(index)
                self.view.topic_input.clear()
            else:
                QMessageBox.critical(self.view, "Error", f"Could not create topic: {result['error']}")
                return
        else:
            # Nếu không, lấy topic đã chọn từ combobox
            target_topic_id = self.view.Topic_opt.currentData()

        if target_topic_id is None:
            # Tự động gán vào topic "Other" nếu không chọn
            QMessageBox.warning(self.view, "Thiếu thông tin", "Bạn phải chọn một chủ đề.")
            return

        result = None
        if self.mode == "add":
            print("DEBUG: Đang ở chế độ ADD, gọi add_word_to_topic...")
            result = self.query_data.add_word_to_topic(
                target_topic_id,
                form_data,
                self._user_context['user_id']
            )
        elif self.mode == "edit":
            print("DEBUG: Đang ở chế độ EDIT, gọi update_word_details...")
            word_id_to_edit = self.word_data_to_edit.get('word_id')
            if not word_id_to_edit:
                QMessageBox.critical(self.view, "Lỗi", "Không tìm thấy ID của từ cần chỉnh sửa.")
                return

            result = self.query_data.update_word_details(word_id_to_edit, form_data)

            # (Nâng cao) Cập nhật lại liên kết topic_word nếu người dùng đổi topic
            self.query_data.update_word_topic_link(word_id_to_edit, target_topic_id)

        # 4. Xử lý kết quả
        if result and result.get("success"):
            self.view.accept()
        else:
            error_msg = result.get('error') if result else "Unknown error"
            QMessageBox.critical(self.view, "Lỗi CSDL", f"Không thể lưu: {error_msg}")