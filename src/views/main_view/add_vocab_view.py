from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog

from src.constants.form_mode import FormMode
from src.controllers.buttonController import buttonController
from src.controllers.main_controller.add_vocab_controller import AddWordController
from src.views.moveable_window import MoveableWindow
from resources import resources_rc


class AddWordDialog(QDialog, MoveableWindow):
    def __init__(self, user_context, parent=None, mode="add", topic_data=None):
        super().__init__(parent)
        uic.loadUi("../UI/forms/add_vocabulary.ui", self)
        MoveableWindow.__init__(self)
        # self.invisible()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # self.user_id_to_edit = None
        # self.word_id_to_edit = None
        # self.topic_id_to_edit = None

        self.buttonController = buttonController(self)
        # Gán nút
        self.Cancel_Btn.clicked.connect(self.buttonController.handle_cancel)
        # Biến để lưu dữ liệu API lấy về
        self.retrieved_word_data = None
        # Giao toàn bộ logic cho Controller
        self.controller = AddWordController(self, user_context, mode, topic_data)

        # self.vocab.textChanged.connect(self.buttonController.handle_add)

        # Tùy chỉnh giao diện theo mode
        if mode == FormMode.ADD:
            self.label.setText("Add New Word")
        elif mode == FormMode.EDIT:
            self.label.setText("Edit Word")

            if not topic_data:
                print("⚠️ topic_data is None")
                self.reject()
                return

            # Load data
            self.vocab.setText(topic_data.get("vocab", ""))
            self.definition.setText(topic_data.get("definition", ""))
            self.example.setText(topic_data.get("example", ""))

        # Gắn sự kiện
        self.SaveVocabBtn.clicked.connect(self.controller.handle_save)

        if parent:
            # Lấy hình chữ nhật (vị trí và kích thước) của cửa sổ cha
            parent_rect = parent.geometry()
            # Lấy hình chữ nhật của chính dialog này
            dialog_rect = self.geometry()
            print(f"DEBUG: PARENT RECT: {parent_rect}")
            print(f"DEBUG: DIALOG RECT: {dialog_rect}")
            # Tính toán vị trí x, y để dialog nằm ở giữa
            move_x = parent_rect.x() + (parent_rect.width() - dialog_rect.width()) // 2
            move_y = parent_rect.y() + (parent_rect.height() - dialog_rect.height()) // 2

            # Di chuyển dialog đến vị trí đã tính toán
            self.move(move_x, move_y)
            print(f"DEBUG: Di chuyển dialog đến vị trí ({move_x}, {move_y})")

    def get_form_data(self):
        """
        Thu thập dữ liệu từ UI để controller có thể lưu.
        Hàm này giờ đã đầy đủ hơn.
        """
        # Nếu đã có dữ liệu từ API, dùng nó làm nền tảng
        if self.retrieved_word_data:
            word_data = self.retrieved_word_data
        else:
            # Nếu không, tạo một cấu trúc rỗng
            word_data = {
                'word_name': self.vocab.text().strip(),
                'pronunciations': [],
                'meanings': [{
                    'part_of_speech': 'N/A',  # Cần thêm widget cho cái này
                    'definition_en': '', 'definition_vi': '',
                    'example_en': '', 'example_vi': ''
                }]
            }

        # Cập nhật lại định nghĩa và ví dụ từ UI (vì người dùng có thể đã sửa)
        # Giả sử bạn có 2 TextEdit: definitionTextEdit và exampleTextEdit
        word_data['meanings'][0]['definition_vi'] = self.definition.toPlainText()
        word_data['meanings'][0]['example_en'] = self.example.toPlainText()

        return word_data