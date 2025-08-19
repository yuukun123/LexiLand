from PyQt5.QtWidgets import QMessageBox, QApplication
# from src.models.user_model import check_login

class RegisterController:
    def __init__(self, view):
        self.view = view

    def handle_register(self, username, password):
        # print(f"DEBUG: Trying login with {username}/{password}")
        # if check_login(username, password):
        #     print("DEBUG: Login success")
        #     self.on_login_success(username)
        # else:
        #     print("DEBUG: Login failed")
        #     self.on_login_failed()
        pass

    # def on_register_success(self, username):
    #     from src.windows.window_manager import open_main_window
    #     QMessageBox.information(self.view, "Login", "✅ Đăng nhập thành công!")
    #     # TODO: Chuyển sang màn hình chính
    #     from src.utils.academic_utils import generate_academic_years_if_needed
    #     generate_academic_years_if_needed()
    #     open_main_window(username)

        # Đóng cửa sổ login
        # self.view.close()

    def on_register_failed(self):
        QMessageBox.warning(self.view, "Login", "❌ Tài khoản hoặc mật khẩu sai!")