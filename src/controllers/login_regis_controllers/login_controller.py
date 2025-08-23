from PyQt5.QtWidgets import QMessageBox
from src.models.login_register.login_register_models import Login_Register_Model
class LoginController:
    def __init__(self, view):
        self.view = view

    def handle_login(self, username_login, password_login):
        if username_login == "" or password_login == "":
            self.on_login_null()
            return
        model = Login_Register_Model()
        print(f"DEBUG: Trying login with {username_login}/{password_login}")
        user = model.check_login(username_login, password_login)
        if user["success"]:
            print("DEBUG: Login success")
            self.on_login_success(username_login)
        else:
            if user == "username_not_found":
                self.on_login_wrong_name_and_password()  # hoặc riêng username
                print("DEBUG: Login failed - user not found")
            elif user == "invalid_credentials":
                self.on_login_wrong_name_and_password()  # hoặc riêng password
                print("DEBUG: Login failed - invalid credentials")
            else:
                self.on_login_failed()
                print("DEBUG: Login failed - unknown error:", user)

        model.close()

    def on_login_success(self, username_login):
        from src.windows.window_manage import open_main_window
        QMessageBox.information(self.view, "Login", "✅ login success!")

        # mở main window
        open_main_window(username_login)

        # đóng login
        self.view.close()

    def on_login_wrong_name_and_password(self):
        self.view.errors_5.setText("wrong username")
        self.view.errors_6.setText("wrong password")
        self.view.errors_5.show()
        self.view.errors_6.show()
        print("wrong username and password")

    def on_login_null(self):
        self.view.errors_5.setText("please enter username and password!")
        self.view.errors_6.setText("please enter username and password!")
        self.view.errors_5.show()
        self.view.errors_6.show()
        print("please enter username and password!")

    def on_login_failed(self):
        QMessageBox.warning(self.view, "Login", "❌ login failed!")