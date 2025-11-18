import os

# DÒNG 2: Import và gọi load_dotenv() NGAY LẬP TỨC
from dotenv import load_dotenv
load_dotenv()

print(f"Giá trị GOOGLE_API_KEY từ môi trường: {os.getenv('GOOGLE_API_KEY')}")

import sys
import asyncio
import qasync  # <-- Import thư viện mới
from PyQt5 import QtWidgets, QtCore
from src.views.login_regis_view.login_regis import Login_and_Register_Window

def load_stylesheet(filename):
    """Đọc và trả về nội dung của file stylesheet."""
    try:
        with open(filename, "r") as f:
            return f.read()
    except FileNotFoundError:
        print(f"CẢNH BÁO: Không tìm thấy file stylesheet: {filename}")
        return ""

# Hàm main bây giờ sẽ là một coroutine
async def main():
    """
    Hàm chính bất đồng bộ để khởi tạo và chạy ứng dụng.
    """
    # Đoạn code boilerplate để quản lý việc đóng ứng dụng một cách an toàn
    def close_future(future, loop):
        loop.call_later(10, future.cancel)
        future.cancel()

    # Lấy vòng lặp sự kiện hiện tại do qasync cung cấp
    loop = asyncio.get_event_loop()
    future = asyncio.Future()

    # Tạo đối tượng QApplication
    # Dùng QApplication.instance() để tránh tạo nhiều instance nếu được gọi lại
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

    app = QtWidgets.QApplication(sys.argv)

    stylesheet = load_stylesheet("UI/css/style_scroll.css")  # Đảm bảo đường dẫn đúng

    # 2. Áp dụng stylesheet cho toàn bộ ứng dụng
    if stylesheet:
        app.setStyleSheet(stylesheet)
        print("DEBUG: Đã áp dụng stylesheet toàn cục.")

    # Kết nối tín hiệu aboutToQuit của app với hàm dọn dẹp
    # để vòng lặp asyncio có thể kết thúc khi cửa sổ cuối cùng đóng lại.
    app.aboutToQuit.connect(lambda: close_future(future, loop))

    # --- KHỞI TẠO CỬA SỔ ĐẦU TIÊN CỦA BẠN ---
    # Thay thế open_login_window() bằng cách tạo instance trực tiếp
    # Điều này giúp giữ tham chiếu đến cửa sổ và tránh bị xóa nhầm
    login_window = Login_and_Register_Window()
    login_window.show()

    # Đợi cho đến khi ứng dụng sẵn sàng để thoát
    await future
    return True


if __name__ == "__main__":
    try:
        # Sử dụng qasync.run() thay vì app.exec_()
        # Nó sẽ chạy vòng lặp sự kiện "lai"
        qasync.run(main())
    except asyncio.exceptions.CancelledError:
        # Bắt lỗi này khi người dùng đóng ứng dụng
        sys.exit(0)
    except Exception as e:
        print(f"Đã xảy ra lỗi không mong muốn ở cấp cao nhất: {e}")
        sys.exit(1)
