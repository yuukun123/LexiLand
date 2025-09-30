import smtplib
from email.message import EmailMessage

SENDER_EMAIL = "lexiland.app@gmail.com"
SENDER_PASSWORD = "zcdi medj umsi dylk"

def send_otp_email(receiver_email, otp_code):
    try:
        # Tạo đối tượng email
        msg = EmailMessage()
        msg['Subject'] = f"Mã xác thực OTP của bạn là {otp_code}"
        msg['From'] = SENDER_EMAIL
        msg['To'] = receiver_email

        # Thiết lập nội dung email
        msg.set_content(f"""
        Hello,

        Thank you for using our application.
        Your One-Time Password (OTP) is:

        {otp_code}
        
        This code is valid for 5 minutes. Please do not share this code with anyone.
        
        Best regards,
        The Development Team.
        """)

        # Kết nối đến server SMTP của Gmail và gửi email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
        return True

    except Exception as e:
        print(f"Lỗi khi gửi email: {e}")
        return False