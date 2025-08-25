import sqlite3
import os

class QueryData:
    def __init__(self):
        # lấy đường dẫn đến thư mục chứ file hiện tại
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # lùi 1 bước về thư muc models
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


    def get_user_by_username(self, username):
        cursor = self.connection.cursor()
        try:
            cursor.execute("SELECT user_id, user_name FROM users WHERE user_name = ?", (username,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"Database error in get_user_by_username: {e}")
            return None

    def get_all_topics_with_word_count(self, user_id):  # Đổi tên hàm cho rõ nghĩa
        """
        Lấy tất cả các chủ đề của một người dùng, kèm theo số lượng từ trong mỗi chủ đề.
        """
        cursor = self.connection.cursor()
        try:
            # Sửa lỗi: Dùng """...""" cho chuỗi nhiều dòng
            # Tối ưu: Thêm t.topic_name vào GROUP BY
            sql_query = """
                SELECT 
                    t.topic_id, 
                    t.topic_name, 
                    COUNT(tw.word_id) as word_count
                FROM 
                    topics t
                LEFT JOIN 
                    topic_word tw ON t.topic_id = tw.topic_id
                WHERE 
                    t.user_id = ?
                GROUP BY 
                    t.topic_id, t.topic_name
                ORDER BY 
                    CASE WHEN t.topic_name = "Other" THEN 0 ELSE 1 END,
                    t.created_at DESC
            """
            cursor.execute(sql_query, (user_id,))

            rows = [dict(row) for row in cursor.fetchall()]
            return rows

        except sqlite3.Error as e:
            print(f"Database error in get_all_topics_with_word_count: {e}")
            return []