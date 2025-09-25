import random
from datetime import timedelta, datetime

from PyQt5 import uic
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import QMessageBox

from src.controllers.main_controller.practice_controller import PracticeController
from src.models.query_data.query_data import QueryData
from src.utils.username_ui import set_user_info
from src.views.moveable_window import MoveableWindow
from src.controllers.buttonController import buttonController
from src.utils.go_back import BaseWindow

class PracticeWindow(BaseWindow, MoveableWindow):
    def __init__(self, user_context, topics, parent=None):
        super().__init__(parent)
        uic.loadUi("../UI/forms/practice.ui", self)
        MoveableWindow.__init__(self)
        self._user_context = user_context
        self.username = self._user_context["user_name"]
        self.query_data = QueryData()
        topic_ids = []
        for t in topics:
            self.topic_name = t["name"]
            self.topic_id = t["id"]
            topic_ids.append(self.topic_id)
            print(f"DEBUG: PRACTICE FOR TOPIC topic {self.topic_name} id {self.topic_id} ")
        self.go_back.clicked.connect(self.stop_learning)

        # Thêm frameless + trong suốt
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(1.0)

        set_user_info(self.username_label, self.username)

        self.buttonController = buttonController(self)
        self.practice_controller = PracticeController(self, self._user_context, topic_ids)
        self.current_index = 0
        self.answer_buttons = [self.answer1, self.answer2, self.answer3, self.answer4]
        self.load_question()

        self.closeBtn.clicked.connect(self.buttonController.handle_close)
        self.hideBtn.clicked.connect(self.buttonController.handle_hidden)
        self.logout.clicked.connect(self.buttonController.handle_logout)
        self.stop_practice_btn.clicked.connect(self.stop_learning)

    def load_question(self):
        q = self.practice_controller.get_question(self.current_index)
        print(f"DEBUG: LIST QUESTION {q}")
        if not q:
            self.current_index = 0
            q = self.practice_controller.get_question(self.current_index)
            if not q:
                QMessageBox.information(self, "Done", "Bạn đã hoàn thành vòng ôn tập!")
                return

        for btn in self.answer_buttons:
            btn.setStyleSheet("background-color: rgb(217, 217, 217);")
            btn.setEnabled(True)
        self.question_label.setText(q["question"])
        self.type_of_word.setText(q["part_of_speech"])

        answers = q["wrong_answers"] + [q["correct_answer"]]
        random.shuffle(answers)

        for btn, ans in zip(self.answer_buttons, answers):
            btn.setText(ans)
            btn.setProperty("is_correct", ans == q["correct_answer"])
            btn.clicked.disconnect() if btn.receivers(btn.clicked) > 0 else None
            btn.clicked.connect(self.check_answer)

    def check_answer(self):
        sender = self.sender()
        q = self.practice_controller.get_question(self.current_index)
        if not q:
            return
        correct_streak = q.get("correct_streak", 0)
        total_incorrect_count = q.get("total_incorrect_count", 0)
        srs_level = q.get("srs_level", 0)
        is_mastered = q.get("is_mastered", 0)
        intervals = [
            timedelta(minutes=5),   # lần đầu
            timedelta(minutes=30),  # lần 2
            timedelta(hours=12),    # lần 3
            timedelta(days=1),      # lần 4
            timedelta(days=2),      # lần 5
            timedelta(days=4),      # lần 6
            timedelta(days=7),      # lần 7
            timedelta(days=15),     # lần 8
        ]
        if sender.property("is_correct"):
            correct_streak += 1
            srs_level += 1
            sender.setStyleSheet("background-color: green; color: white;")
            if srs_level >= len(intervals):
                is_mastered = 1
                next_review_at = "9999-12-31 23:59:59"
            else:
                next_review_at = datetime.now() + intervals[srs_level]
            for btn in self.answer_buttons:
                btn.setEnabled(False)
            self.current_index += 1
            QTimer.singleShot(700, self.load_question)
        else:
            correct_streak = 0
            srs_level = 0
            is_mastered = 0
            total_incorrect_count += 1
            next_review_at = datetime.now() + timedelta(minutes=5)
            sender.setStyleSheet("background-color: red; color: white;")

        update_data = {
        "word_id": q["word_id"],
        "user_id": self._user_context["user_id"],
        "srs_level": srs_level,
        "correct_streak": correct_streak,
        "total_incorrect_count": total_incorrect_count,
        "is_mastered": is_mastered,
        "last_reviewed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "next_review_at": next_review_at
        }
        q["srs_level"] = srs_level
        q["correct_streak"] = correct_streak
        q["total_incorrect_count"] = total_incorrect_count
        q["is_mastered"] = is_mastered
        q["last_reviewed_at"] = update_data["last_reviewed_at"]
        q["next_review_at"] = update_data["next_review_at"]
        self.query_data.update_word_stats(update_data)
        print(update_data)
    def stop_learning(self):
        reply = QMessageBox.question(
        self,
        "Stop learning",
        "Are you sure stop learn?",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.current_index = 0
            if self.parent:
                self.parent.show()
            self.close()