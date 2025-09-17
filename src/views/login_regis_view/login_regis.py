from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QLineEdit

from src.controllers.login_regis_controllers.login_controller import LoginController
from src.controllers.login_regis_controllers.register_controller import RegisterController
from src.views.moveable_window import MoveableWindow
from src.controllers.buttonController import buttonController
from src.utils.changeTab import MenuNavigator

class Login_and_Register_Window(QMainWindow , MoveableWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("../UI/forms/login_register.ui", self)
        MoveableWindow.__init__(self)

        # bên login đặt mặc định ẩn khi mở vì login luôn mở lên đầu tiên
        self.errors_5.hide()
        self.errors_6.hide()

        # Thêm frameless + trong suốt
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(1.0)

        # Tạo controller, truyền self vào
        self.buttonController = buttonController(self)
        self.login_controller = LoginController(self)
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
        self.closeBtn.clicked.connect(self.buttonController.handle_close)
        self.hideBtn.clicked.connect(self.buttonController.handle_hidden)

        #debug
        self.sign_up_link.clicked.connect(lambda: print("Sign up clicked"))
        self.login_link.clicked.connect(lambda: print("Login clicked"))

        buttons = [
            self.login_link, self.sign_up_link
        ]
        index_map = {
            self.login_link: self.stackedWidget.indexOf(self.login_page),
            self.sign_up_link: self.stackedWidget.indexOf(self.sign_up_page)
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