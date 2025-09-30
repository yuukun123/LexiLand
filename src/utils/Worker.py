from PyQt5.QtCore import QObject, pyqtSignal
from src.utils.email_sender import send_otp_email
from src.services.query_data.query_data import QueryData

class EmailWorker(QObject):
    finished = pyqtSignal(bool)
    def __init__(self, email, otp_code):
        super().__init__()
        self.email = email
        self.otp_code = otp_code


    def run(self):
        print(f"Worker: Bắt đầu gửi email tới {self.email} trong một thread riêng...")
        success = send_otp_email(self.email, self.otp_code)
        print(f"DEBUG: RESEND OTP CODE: {self.otp_code}")
        self.finished.emit(success)

class CheckEmailWorker(QObject):
    finished = pyqtSignal(bool)

    def __init__(self, email):
        super().__init__()
        self.email = email

    def run(self):
        print(f"Worker: Đang kiểm tra email {self.email} trong database...")
        exists = QueryData.check_email_exist(self.email)
        self.finished.emit(exists)