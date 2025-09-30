import random
import time

class OTPService:
    def __init__(self, expiry_time_seconds=60, max_attempts=3, lock_time_seconds=300, resend_limit = 3, resend_window = 600):
        self.pending_otps = {}
        self.EXPIRY_TIME_SECONDS = expiry_time_seconds
        self.MAX_ATTEMPTS = max_attempts
        self.LOCK_TIME_SECONDS = lock_time_seconds
        self.locked_users = {}
        self.RESEND_LIMIT = resend_limit
        self.RESEND_WINDOW = resend_window
        self.resend_attempts = {}

    def generate_and_store_otp(self, identifier, user_data):
        if identifier in self.locked_users:
            if time.time() - self.locked_users[identifier] < self.LOCK_TIME_SECONDS:
                return None
            else:
                del self.locked_users[identifier]

        can_resend, msg = self.can_resend(identifier)
        if not can_resend:
            return None

        code = str(random.randint(100000, 999999))
        self.pending_otps[identifier] = {
            'code': code,
            'timestamp': time.time(),
            'data': user_data,
            'attempts': 0
        }
        # Debug log
        print(f"[OTPService] Generated OTP for {identifier}: {code}")
        print(f"[OTPService] pending_otps now: {self.pending_otps}")
        print(f"[OTPService] self instance id: {id(self)}")
        return code

    def verify_otp(self, identifier, user_otp):
        print(f"[OTPService] Verifying OTP {user_otp} for {identifier} in service {id(self)}")
        print(f"[OTPService] Current pending_otps: {self.pending_otps}")
        if identifier in self.locked_users:
            if time.time() - self.locked_users[identifier] < self.LOCK_TIME_SECONDS:
                return False, "Too many failed attempts. Try again later.", None
            else:
                del self.locked_users[identifier]

        if identifier not in self.pending_otps:
            return False, "OTP request not found or expired.", None

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
                print("DEBUG: LOCKED USER")
                self.locked_users[identifier] = time.time()  # khóa trong 5 phút
                del self.pending_otps[identifier]
                return False, "Too many incorrect attempts. Locked for 5 minutes.", None
            print(f"DEBUG: ATTEMPTS USER CLICKED INCORRECT: {otp_info['attempts']}")
            return False, "Invalid OTP.", None

    def can_resend(self, identifier):
        now = time.time()
        attempts = self.resend_attempts.get(identifier, [])
        attempts = [t for t in attempts if now - t < self.RESEND_WINDOW]
        if len(attempts) >= self.RESEND_LIMIT:
            return False, "Too many resend attempts. Please try again later."
        attempts.append(now)
        self.resend_attempts[identifier] = attempts
        return True, None