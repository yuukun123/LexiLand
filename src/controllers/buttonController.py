from PyQt5.QtCore import QPropertyAnimation

class buttonController:
    def __init__(self, view):
        self.view = view

    def handle_cancel(self):
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

    # trong buttonController.py

    def toggle_maximize_restore(self):
        # self.view ở đây là MainWindow
        if self.view.isMaximized():
            self.view.showNormal()
            self.view.maximizeBtn.show()
            self.view.restoreBtn.hide()

            # --- THÔNG BÁO CHO HỆ THỐNG MINI-SIZE ---
            # Khi khôi phục từ maximized, ta coi như nó không còn ở mini-size nữa
            if self.view.is_mini_size:
                self.view.is_mini_size = False
                self.view.size_state_changed.emit(False)  # Phát tín hiệu

        else:
            # Trước khi phóng to, đảm bảo nó không ở trạng thái mini
            if self.view.is_mini_size:
                self.view.toggle_mini_restore()  # Quay về kích thước thường trước

            self.view.showMaximized()
            self.view.maximizeBtn.hide()
            self.view.restoreBtn.show()


