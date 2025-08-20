from src.views.login_regis_view.login_regis import Login_and_Register_Window
from src.views.main_view.main_view import MainWindow
from src.controllers.login_regis_controllers.login_controller import LoginController

def open_login_window():
    window = Login_and_Register_Window()
    controller = LoginController(window)
    window.controller = controller
    window.show()
    return window

def open_main_window(username_login):
    window = MainWindow(username_login)
    window.show()
    return window