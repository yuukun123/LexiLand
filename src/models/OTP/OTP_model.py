from PyQt5.QtCore import QTimer, QThread
from PyQt5.QtWidgets import QMessageBox

from src.utils.Worker import EmailWorker
from src.services.query_data.query_data import QueryData
from src.utils.OTP_service import OTPService


class OTP_model:
    def __init__(self, view, otp_service):
        self.view = view
        self.main_window_instance = None
        self.query_data = QueryData()
        self.otp_service = otp_service
        self.current_email = None
        self.view.error_8.hide()

        self.resend_thread = None
        self.resend_worker = None
        self.countdown_seconds = 60
        self.countdown_timer = QTimer(self.view)
        self.countdown_timer.timeout.connect(self.update_countdown)
        print(f"[OTP_model] Created with otp_service id: {id(otp_service)}")


    def set_email(self, email):
        self.current_email = email.strip().lower()

    def start_countdown(self):
        self.countdown_seconds = 30
        self.view.resend_code.hide()
        self.view.resend_code.setDisabled(True)
        self.view.countdown_label.show()
        self.countdown_timer.start(1000)

    def update_countdown(self):
        if self.countdown_seconds > 0:
            mins, secs = divmod(self.countdown_seconds, 60)
            self.view.countdown_label.setText(f"Resend available in: {mins:02d}:{secs:02d}")
            self.countdown_seconds -= 1
        else:
            self.countdown_timer.stop()
            self.view.countdown_label.setText("Didn't receive the code?")
            self.view.resend_code.show()
            self.view.resend_code.setDisabled(False)
    def get_entered_otp(self):
        return self.view.enter_code.text().strip()
    def validate_and_accept(self):
        entered_otp = self.get_entered_otp()
        print(f"[OTP_model] Validating entered OTP: {entered_otp}, using otp_service id: {id(self.otp_service)}")
        if not entered_otp:
            self.view.error_8.setText("Please enter the OTP code.")
            self.view.error_8.show()
            return

        if not entered_otp.isdigit() or len(entered_otp) != 6:
            self.view.error_8.setText("OTP must be a 6-digit number.")
            self.view.error_8.show()
            return
        success, message, user_data = self.otp_service.verify_otp(self.current_email, entered_otp)
        if not success:
            self.view.error_8.setText(message)
            self.view.error_8.show()
            return
        self.view.error_8.clear()
        print("DEBUG: OTP VERIFIED SUCCESSFULLY!", user_data)
        QMessageBox.information(self.view,"Successfully","OTP verified successfully !")
        self.view.stackedWidget.setCurrentWidget(self.view.reset_pass_page)
        return True
    def handle_resend_request(self):
        self.view.error_8.hide()
        self.view.resend_code.setDisabled(True)
        self.view.vertify_btn.setDisabled(True)
        new_otp_code = self.otp_service.generate_and_store_otp(self.current_email, {'email': self.current_email})
        if not new_otp_code:
            self.view.countdown_label.setText("Too many resend attempts. Please try again later.")
            self.view.resend_code.setDisabled(True)
            return
        # Bắt đầu gửi email trong một thread riêng
        self.resend_thread = QThread()
        self.resend_worker = EmailWorker(self.current_email, new_otp_code)
        self.resend_worker.moveToThread(self.resend_thread)

        self.resend_thread.started.connect(self.resend_worker.run)
        self.resend_worker.finished.connect(self.on_resend_finished) # Kết nối với hàm xử lý kết quả

        # Dọn dẹp
        self.resend_worker.finished.connect(self.resend_thread.quit)
        self.resend_worker.finished.connect(self.resend_worker.deleteLater)
        self.resend_thread.finished.connect(self.resend_thread.deleteLater)

        self.resend_thread.start()

    def on_resend_finished(self, success):
        """Hàm này được gọi khi thread gửi email hoàn thành."""
        if success:
            print("A new OTP has been sent to your email.")
            self.start_countdown()
        else:
            print("Error", "Failed to send new OTP. Please try again.")
            # Kích hoạt lại nút gửi lại nếu thất bại
            self.view.resend_code.setDisabled(False)
            self.view.vertify_btn.setDisabled(False) # Kích hoạt lại nút verify
            self.view.countdown_label.setText("Please try to resend the code.")
