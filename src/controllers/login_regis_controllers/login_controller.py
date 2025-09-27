from PyQt5.QtWidgets import QMessageBox
from src.services.login_register.login_register import Login_Register
from src.services.query_data.query_data import QueryData

class LoginController:
    def __init__(self, view):
        self.view = view
        self.main_window_instance = None
        self.query_data = QueryData()

    def handle_login(self, username_login, password_login):
        if username_login == "" or password_login == "":
            self.on_login_null()
            return
        model = Login_Register()
        print(f"DEBUG: Trying login with {username_login}/{password_login}")
        user = model.check_login(username_login, password_login)
        if user["success"]:
            print("DEBUG: Login success")
            self.on_login_success(username_login)
        else:
            if user["error"] == "invalid_credentials":
                self.on_login_wrong_name_and_password()  # hoặc riêng username
                print("DEBUG: Login failed - user not found")
            elif user["error"] == "incorrect_password":
                self.on_login_wrong_name_and_password()  # hoặc riêng password
                print("DEBUG: Login failed - invalid credentials")
            else:
                self.on_login_failed()
                print("DEBUG: Login failed - unknown error:", user)
        model.close()

    def on_login_success(self, username_login):
        from src.windows.window_manage import open_main_window
        QMessageBox.information(self.view, "Login", "✅ login success!")
        try:
            print(f"DEBUG: Login success for user '{username_login}'")
            user_context = self.query_data.get_user_by_username(username_login)
            if not user_context:
                print(f"LỖI: Không tìm thấy thông tin user '{username_login}'.")
                return
            self.main_window_instance = open_main_window(username_login)
            self.view.close()
            print("DEBUG: MainWindow instance created via window_manage and shown.")
        except Exception as e:
            print("ERROR while opening main window:", e)
            self.view.show()

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