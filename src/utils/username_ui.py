def set_user_info(username_label, username):
    username_lb = username.lower()
    username_label.setText(f"👤 <b>{username_lb}</b>")