def open_login_window():
    window = LoginWindow()
    controller = LoginController(window)
    window.controller = controller
    window.show()
    return window

def open_main_window(username):
    window = MainWindow(username)
    window.show()
    return window