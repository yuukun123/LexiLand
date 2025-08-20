import re

def check_password(password):
    regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$'
    return re.match(regex, password) is not None

def check_email(email):
    pattern = (
        r'^[A-Za-z0-9._%+-]+@'
        r'(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+'
        r'[A-Za-z]{2,}$'
    )
    return re.match(pattern, email) is not None