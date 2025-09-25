from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QDialog, QScrollArea, QWidget,
    QVBoxLayout, QGridLayout, QCheckBox, QMessageBox
)
import sys
from src.models.query_data.query_data import QueryData
from src.views.main_view.practice_view import PracticeWindow


class PracticeOtpController:
    def __init__(self, view, user_context, parent = None):
        self.view = view
        self._user_context = user_context
        user_id = self._user_context['user_id']
        self.user_name = self._user_context['user_name']
        self.query_data = QueryData()
        topics = self.query_data.get_list_topic(user_id)
        self.topic_checkboxes = []
        self.load_topic_into_dialog(topics)

    def load_topic_into_dialog(self, topics):
        # Tạo scroll area
        scroll = self.view.scrollArea
        scroll.setWidgetResizable(True)

        # Container để chứa grid
        container = self.view.container
        grid = QGridLayout(container)
        grid.setAlignment(Qt.AlignTop | Qt.AlignCenter)
        grid.setHorizontalSpacing(60)         # khoảng cách giữa 2 cột
        grid.setVerticalSpacing(30)           # khoảng cách giữa các hàng
        grid.setContentsMargins(0, 5, 0, 0)  # lề trong layout



        for i, topic in enumerate(topics):
            checkbox = QCheckBox(topic["topic_name"])
            checkbox.topic_id = topic["topic_id"]
            if topic["word_count"] == 0:
                checkbox.setEnabled(False)
            # To chữ
            font = checkbox.font()
            font.setPointSize(12)
            checkbox.setFont(font)
            checkbox.setStyleSheet("""
                QCheckBox::indicator {
                width: 20px;
                height: 20px;
                }
            """)
            row = i // 2
            col = i % 2
            grid.addWidget(checkbox, row, col)
            self.topic_checkboxes.append(checkbox)
        scroll.setWidget(container)
    def get_selected_topics(self):
        selected = []
        print("DEBUG checkboxes:", self.topic_checkboxes)
        for checkbox in self.topic_checkboxes:
            print("DEBUG checkbox:", checkbox.text(), "checked:", checkbox.isChecked())
            if checkbox.isChecked():
                selected.append({
                    "id": checkbox.topic_id,
                    "name": checkbox.text()
                })
        return selected
    def handle_practice(self):
        selected_topics = self.get_selected_topics()
        print(selected_topics)
        if not selected_topics:
            QMessageBox.critical(self.view, "Reminder", "Please choose topic that you need practice!")
            return
        if not self._user_context:
            # Sử dụng self._user_context để lấy username cho thông báo lỗi
            user_name_for_msg = self.user_name # Hoặc một giá trị mặc định
            QMessageBox.critical(self.view, "Lỗi nghiêm trọng", f"Không thể tìm thấy dữ liệu cho người dùng '{user_name_for_msg}'.")
            return
        try:
            current_username = self._user_context.get('user_name')
            user_id = self._user_context.get('user_id')
            parent_window = self.view.parentWidget()
            self.practice_window = PracticeWindow(user_context = self._user_context, topics = selected_topics, parent=parent_window)
            self.practice_window.practice_controller.setup_for_user(self._user_context)
            print("DEBUG: practice_window created", self.practice_window)
            if parent_window:
                parent_window.hide()
            self.view.close()
            self.practice_window.show()
            print("DEBUG: practice_window show called")
        except Exception as e:
            print("ERROR while opening topic window:", e)
            self.view.show()

