import random

from src.models.query_data.query_data import QueryData


class PracticeController:
    def __init__(self, parent, user_context, topic_ids):
        print("DEBUG: VocabController.__init__ Bắt đầu.")
        self.parent = parent
        self.query_data = QueryData()
        self._user_context = user_context
        self.user_id = user_context["user_id"]
        self.topic_ids = topic_ids
        self.questions = self._prepare_questions()

    def setup_for_user(self, user_context):
        print(f"DEBUG: VocabController.setup_for_user được gọi với context: {user_context}")
        self._user_context = user_context
        if not self._user_context or 'user_id' not in self._user_context:
            print("LỖI: user_context không hợp lệ hoặc thiếu user_id.")
            return

    def _prepare_questions(self):
        questions = []
        list_word = self.query_data.get_list_words_for_practice(self.user_id, self.topic_ids)
        for word in list_word:
            wrong_defs = self.query_data.get_wrong_definitions(word["id"], word["name"])
            if len(wrong_defs) < 3:
                continue  # bỏ qua nếu chưa đủ dữ liệu
            # lấy 3 nghĩa sai ngẫu nhiên
            wrong_answers = random.sample(wrong_defs, 3)
            questions.append({
                "word_id": word["id"],
                "question": word["name"],
                "correct_answer": word["definition_text"],
                "wrong_answers": wrong_answers,
                "part_of_speech": word["part_of_speech"]
            })
        return questions


    def get_question(self, index):
        if 0 <= index < len(self.questions):
            return self.questions[index]
        return None


