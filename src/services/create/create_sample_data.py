import os
import sqlite3

class CreateSampleData:
    def __init__(self):
        # lấy đường dẫn đến thư mục chứ file hiện tại
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # lùi 1 bước về thư mục services
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

        # Kết nối CSDL
        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row  # trả về dạng dict-like thay vì tuple
        self.cursor = self.connection.cursor()
        print(f"connect database '{db_path}' successful")

    def create_sample_data(self):
        self.cursor.execute("""
                INSERT INTO topics (topic_name, created_at, user_id)
                VALUES 
                        ('Topic 1', datetime('now'), 1),
                        ('Topic 1', datetime('now'), 2),
                        ('Topic 2', datetime('now'), 1),
                        ('Topic 2', datetime('now'), 2),
                        ('Topic 3', datetime('now'), 1),
                        ('Topic 3', datetime('now'), 2),
                        ('Topic 4', datetime('now'), 1),
                        ('Topic 4', datetime('now'), 2),
                        ('Topic 5', datetime('now'), 1),
                        ('Topic 5', datetime('now'), 2),
                        ('Topic 6', datetime('now'), 1),
                        ('Topic 6', datetime('now'), 2),
                        ('Topic 7', datetime('now'), 1),
                        ('Topic 7', datetime('now'), 2),
                        ('Topic 8', datetime('now'), 1),
                        ('Topic 8', datetime('now'), 2),
                        ('Topic 9', datetime('now'), 1),
                        ('Topic 9', datetime('now'), 2),
                        ('Topic 10', datetime('now'), 1),
                        ('Topic 10', datetime('now'), 2),
                        ('Topic 11', datetime('now'), 1),
                        ('Topic 11', datetime('now'), 2),
                        ('Topic 12', datetime('now'), 1),
                        ('Topic 12', datetime('now'), 2)
                        
            """)
        self.connection.commit()
        print("Sample data inserted successfully.")

if __name__ == "__main__":
    sample = CreateSampleData()  # phải khởi tạo object
    sample.create_sample_data()  # gọi hàm instance