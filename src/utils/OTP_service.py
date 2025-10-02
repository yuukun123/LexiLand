import random
import time

from PyQt5.QtWidgets import QMessageBox

from src.services.query_data.query_data import QueryData

class OTPService:
    def __init__(self, view, expiry_time_seconds=300, max_attempts=3, lock_time_seconds=300, resend_limit = 3, resend_window = 600):
        self.view = view
        self.pending_otps = {}
        self.EXPIRY_TIME_SECONDS = expiry_time_seconds
        self.MAX_ATTEMPTS = max_attempts
        self.LOCK_TIME_SECONDS = lock_time_seconds
        self.RESEND_LIMIT = resend_limit
        self.RESEND_WINDOW = resend_window
        self.query_data = QueryData()


    def is_locked(self, user_id):
        locked_until = self.query_data.get_locked_until(user_id)
        print("[DEBUG] Locked until:", self.query_data.get_locked_until(user_id), "now:", time.time())
        return locked_until and time.time() < locked_until
    def lock_user(self, user_id):
        self.query_data.lock_user(user_id, self.LOCK_TIME_SECONDS)
        QMessageBox.information(self.view,"Lock User", "User has been locked for 5 minute. PLease try again later!")
        self.view.stackedWidget.setCurrentWidget(self.view.login_page)
        print("DEBUG: LOCKED USER")

    def generate_and_store_otp(self, identifier, user_id, user_data, is_resend=False):
        can_resend, msg = self.can_resend(user_id, is_resend)
        if not can_resend:
            return None
        code = str(random.randint(100000, 999999))
        self.pending_otps[identifier] = {
            'code': code,
            'timestamp': time.time(),
            'data': user_data,
            'attempts': 0,
            'attempts_resend': 0,
            'user_id': user_id
        }
        # Debug log
        print(f"[OTPService] Generated OTP for {identifier}: {code}")
        return code

    def verify_otp(self, identifier, user_otp, user_id):
        print(f"[OTPService] Verifying OTP {user_otp} for {identifier} in service {id(self)}")
        print(f"[OTPService] Current pending_otps: {self.pending_otps}")
        if self.is_locked(user_id):
            return False, "Too many failed attempts. Try again later.", None
        otp_info = self.pending_otps[identifier]
        if time.time() - otp_info['timestamp'] > self.EXPIRY_TIME_SECONDS:
            del self.pending_otps[identifier]
            return False, "OTP has expired.", None

        if user_otp == otp_info['code']:
            user_data = otp_info['data']
            del self.pending_otps[identifier]
            return True, "Verification successful!", user_data
        else:
            otp_info['attempts'] += 1
            if otp_info['attempts'] >= self.MAX_ATTEMPTS:
                self.lock_user(user_id)  # khóa trong 5 phút
                del self.pending_otps[identifier]
                return False, "Too many incorrect attempts. Locked for 5 minutes.", None
            print(f"DEBUG: ATTEMPTS USER CLICKED INCORRECT: {otp_info['attempts']}")
            return False, "Invalid OTP.", None

    # def can_resend(self, user_id, is_resend=False):
    #     now = time.time()
    #     result = self.query_data.get_resend_info(user_id)
    #     if not result:
    #         if is_resend:
    #             self.query_data.insert_resend(user_id, now, 1)   # lần resend đầu tiên
    #         else:
    #             self.query_data.insert_resend(user_id, now, 0)   # lần generate OTP đầu
    #         return True, None
    #     attempts, last_resend = result
    #     if last_resend and now - last_resend < self.RESEND_WINDOW:
    #         if is_resend:
    #             if attempts >= self.RESEND_LIMIT:
    #                 return False, "Too many resend attempts. Please try again later."
    #             self.query_data.update_resend(user_id,attempts + 1,now)
    #         else:
    #             # Không phải resend (chỉ generate OTP ban đầu) thì giữ nguyên attempts, không reset
    #             return attempts < self.RESEND_LIMIT, None
    #     else:
    #         if is_resend:
    #             self.query_data.update_resend(user_id, 1, now)
    #         else:
    #             self.query_data.update_resend(user_id, 0, now)
    #     return True, None

    def can_resend(self, user_id, is_resend=False):
        now = time.time()

        # Bước 1: Lấy tất cả trạng thái của user (bao gồm cả thông tin khóa)
        attempts, last_resend, locked_until = self.query_data.get_user_status(user_id)

        # Bước 2: KIỂM TRA LOCK ĐẦU TIÊN VÀ QUAN TRỌNG NHẤT
        if locked_until and now < locked_until:
            remaining_time = int(locked_until - now)
            return False, f"Account is locked. Please try again in {remaining_time} seconds."

        # Bước 3: Xử lý user chưa có trong DB (lần đầu tương tác)
        if last_resend is None:
            # Gọi hàm insert_resend đã sửa (chỉ nhận 2 tham số)
            # Logic ở đây là: lần đầu tiên generate OTP sẽ có attempts=0
            # Lần đầu tiên resend sẽ có attempts=1.
            # Hàm insert_resend mới có thể cần sửa lại để nhận attempts.
            # Hoặc đơn giản hơn:
            initial_attempts = 1 if is_resend else 0
            self.query_data.upsert_resend_info(user_id, initial_attempts, now)  # Nên có 1 hàm gộp
            return True, None

        # Bước 4: Xử lý logic Rate Limit
        if now - last_resend < self.RESEND_WINDOW:
            if is_resend:
                # Nếu đạt giới hạn -> KÍCH HOẠT LOCK
                if attempts >= self.RESEND_LIMIT:
                    self.query_data.lock_user(user_id, self.LOCK_TIME_SECONDS)
                    return False, f"Too many resend attempts. Account locked for {self.LOCK_TIME_SECONDS // 60} minutes."

                # Nếu chưa đạt giới hạn -> tăng attempts
                self.query_data.update_resend(user_id, attempts + 1, now)
            # else: không phải resend thì không cần làm gì, cứ cho qua
        else:
            # Hết RESEND_WINDOW, reset lại bộ đếm
            new_attempts = 1 if is_resend else 0
            self.query_data.update_resend(user_id, new_attempts, now)

        return True, None
