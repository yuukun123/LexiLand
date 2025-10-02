import time

from PyQt5.QtWidgets import QMessageBox
from werkzeug.security import generate_password_hash, check_password_hash
from src.services.query_data.query_data import QueryData
import re
import threading
from src.utils.OTP_service import OTPService
from src.utils.email_sender import send_otp_email
from src.models.OTP.OTP_model import OTP_model

class forgotPasswordController:
    def __init__(self, view):
        self.view = view
        self.main_window_instance = None
        self.query_data = QueryData()
        self.otp_service = OTPService(self.view)
        self.otp_model = OTP_model(self.view, self.otp_service)
        self.current_email = None
        self.view.errors_7.hide()

    def check_email(self, email):
        print("DEBUG: START CHECK")
        email_input = email.strip().lower()
        user_id = self.query_data.get_user_id_by_email(email_input)
        if not email_input:
            self.view.errors_7.setText("Please fill in all information")
            self.view.errors_7.show()
            return
        if not re.match(r"^[a-zA-Z0-9._%+-]+@gmail\.com$", email_input):
            self.view.errors_7.setText("Invalid Email")
            self.view.errors_7.show()
            return
        if not self.query_data.check_email_exist(email_input):
            self.view.errors_7.setText("Email not found")
            self.view.errors_7.show()
            return
        locked_until = self.query_data.get_locked_until(user_id)
        if locked_until and time.time() < locked_until:
            QMessageBox.information(self.view,"Lock User", "User has been locked. PLease try again later!")
            self.view.stackedWidget.setCurrentWidget(self.view.login_page)
            return

        self.current_email = email_input
        print("DEBUG: Generating OTP code.....")
        otp_code = self.otp_service.generate_and_store_otp(email_input, user_id, {'email': email_input, 'user_id': user_id}, is_resend=False)
        threading.Thread(target=send_otp_email, args=(email_input, otp_code)).start()
        print(f"DEBUG: OTP CODE HAS BEEN GENERATED: {otp_code}")
        print(f"DEBUG: OTP CODE HAS BEEN SEND TO {email_input}")
        self.otp_model.set_email(self.current_email, is_resend=False)
        self.view.open_send_code()


    def check_new_password(self):
        new_password = self.view.enter_password.text()
        new_cf_password = self.view.enter_cf_password.text()
        if not new_password or not new_cf_password:
            self.view.errors_9.setText("Please fill in all information")
            self.view.errors_9.show()
            return
        if new_password != new_cf_password:
            self.view.errors_9.setText("Password does not match")
            self.view.errors_9.show()
            return
        if len(new_password) < 8:
            self.view.errors_9.setText("Password must be at least 8 characters")
            self.view.errors_9.show()
            return
        pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$'
        if not re.match(pattern, new_password):
            self.view.errors_9.setText(
                "Password must contain upper, lower, digit, and special character"
            )
            self.view.errors_9.show()
            return
        hashed_pw = generate_password_hash(new_password, method="scrypt")
        old_password = self.query_data.get_hashed_password(self.current_email)
        print(f"DEBUG: OLD PASSWORD: {old_password}")
        if check_password_hash(old_password, new_password):
            self.view.errors_9.setText("Old and new passwords cannot match.")
            self.view.errors_9.show()
            return
        result = self.query_data.update_new_password(hashed_pw,self.current_email)
        if result:
            QMessageBox.information(self.view,"Successfully", "Updated password successfully!")
            self.view.stackedWidget.setCurrentWidget(self.view.login_page)
        else:
            print("DEBUG: UPDATE PASSWORD ERROR")
        self.view.errors_9.clear()
        self.view.errors_9.hide()









