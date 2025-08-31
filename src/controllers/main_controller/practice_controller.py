from src.models.query_data.query_data import QueryData


class PracticeController:
    def __init__(self, parent):
        print("DEBUG: VocabController.__init__ Bắt đầu.")
        self.parent = parent
        self.query_data = QueryData()
        self._user_context = None

    def setup_for_user(self, user_context):
        print(f"DEBUG: VocabController.setup_for_user được gọi với context: {user_context}")
        self._user_context = user_context
        if not self._user_context or 'user_id' not in self._user_context:
            print("LỖI: user_context không hợp lệ hoặc thiếu user_id.")
            return