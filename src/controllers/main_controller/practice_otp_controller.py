from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QDialog, QScrollArea, QWidget,
    QVBoxLayout, QGridLayout, QCheckBox
)
import sys
from src.models.query_data.query_data import QueryData


class PracticeOtpController:
    def __init__(self, view, user_context, parent = None):
        self.view = view
        self._user_context = user_context
        user_id = self._user_context['user_id']
        self.query_data = QueryData()
        topics = self.query_data.get_list_topic(user_id)
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
        scroll.setWidget(container)
