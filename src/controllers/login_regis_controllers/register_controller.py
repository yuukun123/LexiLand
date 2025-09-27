from PyQt5.QtWidgets import QMessageBox, QApplication
from src.services.login_register.login_register import Login_Register
from src.utils.check_correct_email_password import check_password, check_email

class RegisterController:
    def __init__(self, view, stacked_widget, login_page):
        self.view = view
        self.stacked_widget = stacked_widget
        self.login_page = login_page

    def handle_register(self, username_register, email_register, password_register, confirm_password_register):
        print(f"DEBUG: Trying login with {username_register}/{password_register}/{confirm_password_register}/{email_register}")
        email_register = email_register.lower()
        if username_register == "" or password_register == "" or confirm_password_register == "" or email_register == "":
            self.on_register_null()
        elif confirm_password_register != password_register:
            self.on_register_conform_password()
            self.clear_register_fields()
        elif check_password(password_register) == False: # check password_register
            self.on_register_password_incorrect()
            self.clear_register_fields()
        elif check_email(email_register) == False: # check email_register
            self.on_register_email_incorrect()
            self.clear_register_fields()
        else:
            model = Login_Register()
            result = model.add_users(username_register, password_register, email_register)
            if result.get("success"):
                print("DEBUG: Register success")
                self.on_register_success(username_register)
            elif result.get("error") == "username_exists":
                print("DEBUG: Register failed - username exists")
                self.on_register_username_exists()
                self.clear_register_fields()
            else:
                print("DEBUG: Register failed")
                self.on_register_failed()
            model.close()

    def on_register_success(self, username):
        QMessageBox.information(self.view, "Register", "✅ Register success!")
        # TODO: Chuyển sang màn login
        self.clear_register_fields()
        self.stacked_widget.setCurrentIndex(self.stacked_widget.indexOf(self.login_page))

    def on_register_null(self):
        self.errors = "❌ please enter username and password!"
        # QMessageBox.warning(self.view, "Register", ")
        self.view.errors_1.setText("please fill all fields!")
        self.view.errors_2.setText("please fill all fields!")
        self.view.errors_3.setText("please fill all fields!")
        self.view.errors_4.setText("please fill all fields!")
        self.view.errors_1.show()
        self.view.errors_2.show()
        self.view.errors_3.show()
        self.view.errors_4.show()

    def on_register_username_exists(self):
        self.view.errors_1.setText("username exists!")
        self.view.errors_1.show()

    def on_register_conform_password(self):
        self.view.errors_2.setText("password doesn't match!")
        self.view.errors_2.show()

    def on_register_password_incorrect(self):
        self.view.errors_3.setText("password must be at least 8 characters and use special characters and numbers and letters!")

    def on_register_email_incorrect(self):
        self.view.errors_4.setText("email incorrect!")
        self.view.errors_4.show()

    def on_register_failed(self):
        QMessageBox.warning(self.view, "Register", "❌ Register failed!")

    def clear_register_fields(self):
        self.view.username_register.clear()
        self.view.email_register.clear()
        self.view.password_register.clear()
        self.view.cf_password_register.clear()
