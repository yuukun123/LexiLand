
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QLineEdit

from src.controllers.login_regis_controllers.login_controller import LoginController
from src.controllers.login_regis_controllers.register_controller import RegisterController
from src.controllers.login_regis_controllers.forgot_password_controller import forgotPasswordController
from src.models.OTP.OTP_model import OTP_model
from src.views.moveable_window import MoveableWindow
from src.controllers.buttonController import buttonController
from src.utils.changeTab import MenuNavigator

class Login_and_Register_Window(QMainWindow , MoveableWindow):
    def __init__(self):
        super().__init__()

        uic.loadUi("UI/forms/login_register.ui", self)
        print("DEBUG:", self.enter_email_page)
        MoveableWindow.__init__(self)

        # bên login đặt mặc định ẩn khi mở vì login luôn mở lên đầu tiên
        self.errors_5.hide()
        self.errors_6.hide()
        self.errors_7.hide()
        self.error_8.hide()
        self.errors_9.hide()

        # Thêm frameless + trong suốt
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(1.0)

        # Tạo controller, truyền self vào
        self.buttonController = buttonController(self)
        self.login_controller = LoginController(self)
        self.forgot_password_controller = forgotPasswordController(self)
        self.register_controller = RegisterController(self, self.stackedWidget, self.login_page)

        #login khi ấn enter
        self.username_login.returnPressed.connect(
            lambda: self.login_controller.handle_login(
                self.username_login.text(), self.password_login.text()
            )
        )
        self.password_login.returnPressed.connect(
            lambda: self.login_controller.handle_login(
                self.username_login.text(), self.password_login.text()
            )
        )
        #signup khi ấn enter
        self.username_register.returnPressed.connect(
            lambda: self.register_controller.handle_register(
                self.username_register.text(), self.email_register.text(), self.password_register.text(), self.cf_password_register.text()
            )
        )
        self.email_register.returnPressed.connect(
            lambda: self.register_controller.handle_register(
                self.username_register.text(), self.email_register.text(), self.password_register.text(), self.cf_password_register.text()
            )
        )
        self.password_register.returnPressed.connect(
            lambda: self.register_controller.handle_register(
                self.username_register.text(), self.email_register.text(), self.password_register.text(), self.cf_password_register.text()
            )
        )
        self.cf_password_register.returnPressed.connect(
            lambda: self.register_controller.handle_register(
                self.username_register.text(), self.email_register.text(), self.password_register.text(), self.cf_password_register.text()
            )
        )

        # Gắn nút
        self.LoginBtn.clicked.connect(
            lambda: self.login_controller.handle_login(
                self.username_login.text(), self.password_login.text()
            )
        )

        self.SignUp_Btn.clicked.connect(
            lambda: self.register_controller.handle_register(
                self.username_register.text(), self.email_register.text(), self.password_register.text(), self.cf_password_register.text()
            )
        )
        # button forgot password
        self.ForgotPassword.clicked.connect(
            self.open_enter_email
        )
        # button check email
        self.confirm_btn.clicked.connect(
            lambda: self.forgot_password_controller.check_email(
                self.enter_email.text()
            )
        )
        self.enter_email.textChanged.connect(self.hide_error)
        self.enter_email.returnPressed.connect(
            lambda: self.forgot_password_controller.check_email(
                self.enter_email.text()
            ))
        # button vertify otp code
        self.vertify_btn.clicked.connect(self.forgot_password_controller.otp_model.validate_and_accept)
        self.enter_code.textChanged.connect(self.hide_error)
        self.enter_code.returnPressed.connect(self.forgot_password_controller.otp_model.validate_and_accept)

        self.resend_code.clicked.connect(self.forgot_password_controller.otp_model.handle_resend_request)

        self.closeBtn.clicked.connect(buttonController.handle_close)
        self.hideBtn.clicked.connect(self.buttonController.handle_hidden)

        # show and hide password
        self.hide_pass.clicked.connect(self.toggle_new_password)
        self.hide_pass_2.clicked.connect(self.toggle_new_cf_password)

        # check reset pass button
        self.set_new_pass_btn.clicked.connect(self.forgot_password_controller.check_new_password)
        self.enter_password.returnPressed.connect(self.forgot_password_controller.check_new_password)
        self.enter_cf_password.returnPressed.connect(self.forgot_password_controller.check_new_password)

        # return to login page button
        self.cancel_btn.clicked.connect(self.return_login_page)
        self.cancel_btn_2.clicked.connect(self.return_login_page)
        self.cancel_btn_3.clicked.connect(self.return_login_page)

        #debug
        self.sign_up_link.clicked.connect(lambda: print("Sign up clicked"))
        self.login_link.clicked.connect(lambda: print("Login clicked"))

        buttons = [
            self.login_link, self.sign_up_link
        ]
        index_map = {
            self.login_link: self.stackedWidget.indexOf(self.login_page),
            self.sign_up_link: self.stackedWidget.indexOf(self.sign_up_page),
        }
        self.menu_nav = MenuNavigator(self.stackedWidget, buttons, index_map, default_button=self.login_link)

        self.stackedWidget.currentChanged.connect(self.on_tab_changed)

        # Chủ động tải Dashboard lần đầu tiên nếu nó là tab mặc định
        if self.stackedWidget.currentWidget() == self.login_page:
            self.on_tab_changed(self.stackedWidget.currentIndex())

    def on_tab_changed(self, index):
        # clear toàn bộ input ở page trước đó
        prev_index = self.stackedWidget.previousIndex if hasattr(self.stackedWidget, "previousIndex") else None
        if prev_index is not None:
            old_widget = self.stackedWidget.widget(prev_index)
            for child in old_widget.findChildren(QLineEdit):
                child.clear()

        # lưu lại index hiện tại
        self.stackedWidget.previousIndex = index

        current_widget = self.stackedWidget.widget(index)
        if current_widget == self.login_page:
            # bên register
            self.errors_1.hide()
            self.errors_2.hide()
            self.errors_3.hide()
            self.errors_4.hide()
            print()
        elif current_widget == self.sign_up_page:
            # bên login
            self.errors_5.hide()
            self.errors_6.hide()
            print()
        elif current_widget == self.enter_email_page:
            self.errors_7.hide()

    def open_enter_email(self):
        print("DEBUG: START OPEN ENTER EMAIL")
        self.stackedWidget.setCurrentIndex(self.stackedWidget.indexOf(self.enter_email_page))
    def open_send_code(self):
        print("DEBUG: START OPEN SEND CODE")
        self.stackedWidget.setCurrentIndex(self.stackedWidget.indexOf(self.send_code_page))
    def return_login_page(self):
        print("DEBUG: START OPEN SEND CODE")
        self.stackedWidget.setCurrentIndex(self.stackedWidget.indexOf(self.login_page))
    def hide_error(self):
        self.errors_7.hide()
        self.error_8.hide()

    def toggle_new_password(self):
        if self.enter_password.echoMode() == QLineEdit.Password:
            self.enter_password.setEchoMode(QLineEdit.Normal)
            path = "UI/icons/eye.svg"
            self.hide_pass.setIcon(QIcon(path))
        else:
            self.enter_password.setEchoMode(QLineEdit.Password)
            path = "UI/icons/eye-off.svg"
            self.hide_pass.setIcon(QIcon(path))

    def toggle_new_cf_password(self):
        if self.enter_cf_password.echoMode() == QLineEdit.Password:
            self.enter_cf_password.setEchoMode(QLineEdit.Normal)
            path = "UI/icons/eye.svg"
            self.hide_pass.setIcon(QIcon(path))
        else:
            self.enter_cf_password.setEchoMode(QLineEdit.Password)
            path = "UI/icons/eye-off.svg"
            self.hide_pass.setIcon(QIcon(path))