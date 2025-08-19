class MenuNavigator:
    def __init__(self, stacked_widget, buttons, index_map, default_button=None):
        self.stacked_widget = stacked_widget
        self.buttons = buttons
        self.index_map = index_map
        self.active_button = None

        for btn in self.buttons:
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, b=btn: self.handle_click(b))

        # Nếu có nút mặc định, chọn ngay
        if default_button and default_button in self.index_map:
            self.handle_click(default_button)

    def handle_click(self, button):
        if button in self.index_map:
            self.stacked_widget.setCurrentIndex(self.index_map[button])
            self.set_active(button)

    def set_active(self, button):
        for btn in self.buttons:
            btn.setChecked(False)
        button.setChecked(True)
        self.active_button = button