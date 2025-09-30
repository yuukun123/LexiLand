import os
import sqlite3
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

class Login_Register:
    def __init__(self):
        # lấy đường dẫn đến thư mục chứ file hiện tại
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # lùi 1 bước về thư muc services
        models_dir = os.path.dirname(script_dir)
        # chốt lại thư mục gốc để chứa folder database
        project_root = os.path.dirname(models_dir)
        # đường dẫn đầy đủ đến thư mục database
        db_folder = os.path.join(project_root, "database")
        # Và cuối cùng, đường dẫn đầy đủ đến file CSDL
        db_path = os.path.join(db_folder, "database.db")

        print(f"Thư mục script hiện tại: {script_dir}")
        print(f"Thư mục gốc của dự án: {project_root}")
        print(f"Đường dẫn CSDL sẽ được tạo tại: {db_path}")

        # Tạo thư mục 'database' trong thư mục gốc nếu nó chưa tồn tại
        os.makedirs(db_folder, exist_ok=True)
        print(f"Thư mục '{db_folder}' đã sẵn sàng.")

        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
        print(f"connect database '{db_path}' successful")

    def check_login(self, username_login, password_login):
        """
        Checks user credentials against the database correctly.
        Returns user info dictionary on success, None on failure.
        """
        cursor = self.cursor
        # Bước 1: Lấy thông tin người dùng bằng username
        # Chúng ta chỉ cần lấy password_hash để kiểm tra
        cursor.execute("""
            SELECT
                user_id AS id,
                user_name,
                password AS password_hash
            FROM
                users
            WHERE
                LOWER(user_name) = LOWER(?)
        """, (username_login,))
        user_data = cursor.fetchone()

        if not user_data:
            print(f"❌ Login failed: User '{username_login}' not found.")
            return {"success": False, "error": "invalid_credentials"}

        # Bước 2: Dùng check_password_hash để so sánh mật khẩu người dùng nhập
        # với chuỗi hash đã lưu trong DB.
        stored_password_hash = user_data['password_hash']

        if check_password_hash(stored_password_hash, password_login):
            print(f"✅ Login success for user '{username_login}'")
            # Trả về một dictionary chứa thông tin người dùng, rất hữu ích cho ứng dụng
            return {"success": True, "user": dict(user_data)}  # luôn có success
        elif not check_password_hash(stored_password_hash, password_login):
            print(f"❌ Login failed for user '{username_login}': Incorrect password.")
            return {"success": False, "error": "incorrect_password"}
        else:
            print(f"❌ Login failed for user '{username_login}': Unknown error.")
            return {"success": False, "error": "unknown_error"}

    def add_users(self, username_register, password_register, email_register):
        try:
            self.cursor.execute("SELECT * FROM users WHERE user_name = ?", (username_register,))
            if self.cursor.fetchone():
                return {"success": False, "error": "username_exists"}

            hashed_password = generate_password_hash(password_register)
            self.cursor.execute("""
                INSERT INTO users (user_name, password, email)
                VALUES (?, ?, ?)
            """, (username_register, hashed_password, email_register))
            self.connection.commit()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}


    def close(self):
        self.connection.close()