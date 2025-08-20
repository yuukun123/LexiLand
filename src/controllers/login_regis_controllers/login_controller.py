from PyQt5.QtWidgets import QMessageBox
from src.models.login_register.login_register_models import Login_Register_Model
class LoginController:
    def __init__(self, view):
        self.view = view

    def handle_login(self, username_login, password_login):
        model = Login_Register_Model()
        print(f"DEBUG: Trying login with {username_login}/{password_login}")
        user = model.check_login(username_login, password_login)
        if user:
            print("DEBUG: Login success")
            self.on_login_success(username_login)
        else:
            print("DEBUG: Login failed")
            self.on_login_failed()
        model.close()

    def on_login_success(self, username_login):
        from src.windows.window_manage import open_main_window
        QMessageBox.information(self.view, "Login", "✅ Đăng nhập thành công!")
        # TODO: Chuyển sang màn hình chính
        open_main_window(username_login)
        # Đóng cửa sổ login
        self.view.close()

    def on_login_failed(self):
        QMessageBox.warning(self.view, "Login", "❌ Tài khoản hoặc mật khẩu sai!")