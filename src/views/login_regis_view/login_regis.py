from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow

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

        # Thêm frameless + trong suốt
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setWindowOpacity(1.0)

        # Tạo controller, truyền self vào
        self.buttonController = buttonController(self)

        # Tạo controller, truyền self vào
        self.login_controller = LoginController(self)
        self.register_controller = RegisterController(self)

        # Gắn nút
        # self.LoginBtn.clicked.connect(lambda: self.controller.handle_login(
        #     self.UserName_login.text(), self.Password_login.text()
        # ))
        self.closeBtn.clicked.connect(self.buttonController.handle_close)
        self.hideBtn.clicked.connect(self.buttonController.handle_hidden)

        buttons = [
            self.login_link, self.sign_up_link
        ]
        index_map = {
            self.login_link: self.stackedWidget.indexOf(self.login_page),
            self.sign_up_link: self.stackedWidget.indexOf(self.sign_up_page)
        }
        self.menu_nav = MenuNavigator(self.stackedWidget, buttons, index_map, default_button=self.login_link)

        # self.sign_up_link.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(1))
        # self.login_link.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(0))

        self.sign_up_link.clicked.connect(lambda: print("Sign up clicked"))
        self.login_link.clicked.connect(lambda: print("Login clicked"))
        #
        # print("login_page index:", self.stackedWidget.indexOf(self.login_page))
        # print("signup_page index:", self.stackedWidget.indexOf(self.sign_up_page))


        self.stackedWidget.currentChanged.connect(self.on_tab_changed)

        # Chủ động tải Dashboard lần đầu tiên nếu nó là tab mặc định
        if self.stackedWidget.currentWidget() == self.login_page:
            self.on_tab_changed(self.stackedWidget.currentIndex())

    def on_tab_changed(self, index):
        current_widget = self.stackedWidget.widget(index)

        if current_widget == self.login_page:
            self.login_controller.handle_login(
                self.userName_login.text(), self.password_login.text()
            )
        elif current_widget == self.sign_up_page:
            self.register_controller.handle_register(
                self.userName_register.text(), self.password_register.text()
            )