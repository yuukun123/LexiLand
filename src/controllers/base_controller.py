# trong src/controllers/base_controller.py
from abc import ABC, abstractmethod
from src.models.query_data.query_data import QueryData  # Import QueryData ở đây


class BaseController(ABC):
    def __init__(self, parent_view):
        """Khởi tạo các thuộc tính chung."""
        self.parent = parent_view
        # Khởi tạo QueryData ngay tại đây, vì tất cả các controller con đều cần nó
        self.query_data = QueryData()
        # Khởi tạo user_context là None
        self._user_context = None

    def setup_for_user(self, user_context):
        """
        Thiết lập controller với thông tin người dùng và tải dữ liệu.
        Đây là hàm được gọi từ bên ngoài để "kích hoạt" controller.
        """
        print(f"DEBUG: {self.__class__.__name__}.setup_for_user được gọi.")
        self._user_context = user_context
        if not self._user_context or 'user_id' not in self._user_context:
            print(f"LỖI trong {self.__class__.__name__}: user_context không hợp lệ.")
            return

        # Gọi các hàm làm mới ngay sau khi thiết lập
        self.refresh_data()

    @abstractmethod
    def _update_stats(self):
        pass

    @abstractmethod
    def _load_and_display_items(self):
        pass

    def refresh_data(self):
        """HÀM DÙNG CHUNG."""
        # ... (Hàm này không thay đổi)
        print(f"DEBUG: {self.__class__.__name__} đang làm mới...")
        if not self._user_context: return
        self._update_stats()
        self._load_and_display_items()