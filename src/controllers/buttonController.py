from PyQt5.QtCore import QPropertyAnimation

class buttonController:
    def __init__(self, view):
        self.view = view

    def handle_cancel(self):
        print(f"DEBUG: Bắt đầu hủy dialog.")
        self.view.reject()

    def handle_ok(self):
        self.view.close()

    def handle_close(self):
        self.view.close()

    def handle_hidden(self):
        self.fade_animation = QPropertyAnimation(self.view, b"windowOpacity")
        self.fade_animation.setDuration(100)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.finished.connect(self._minimize)
        self.fade_animation.start()

    def _minimize(self):
        self.view.showMinimized()
        self.view.setWindowOpacity(1.0)

    def handle_logout(self):
        from src.windows.window_manage import open_login_window
        open_login_window()
        self.view.close()