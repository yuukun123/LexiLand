import sqlite3
import os

def create_table():
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

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    print(f"connect database '{db_path}' successful")
    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            email TEXT NOT NULL,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            topic_id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_name TEXT NOT NULL,
            created_at TEXT,
            user_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(user_id),
            UNIQUE(topic_name, user_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS words (
            word_id INTEGER PRIMARY KEY AUTOINCREMENT,
            word_name TEXT NOT NULL UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pronunciations (
            pronunciation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            word_id INTEGER NOT NULL,
            region TEXT,          -- Vùng miền, ví dụ: 'UK', 'US'
            phonetic_text TEXT,   -- Phiên âm dạng text, ví dụ: '/həˈləʊ/'
            audio_url TEXT,      -- Đường dẫn URL đến file MP3
            FOREIGN KEY(word_id) REFERENCES words(word_id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meanings (
            meaning_id INTEGER PRIMARY KEY AUTOINCREMENT,
            word_id INTEGER NOT NULL,
            part_of_speech TEXT NOT NULL,
            FOREIGN KEY(word_id) REFERENCES words(word_id) on DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS definition (
            definition_id INTEGER PRIMARY KEY AUTOINCREMENT,
            meaning_id INTEGER NOT NULL,
            language TEXT NOT NULL, -- 'en', 'vi'
            definition_text TEXT NOT NULL,
            FOREIGN KEY(meaning_id) REFERENCES meanings(meaning_id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
            CREATE TABLE IF NOT EXISTS examples (
                example_id INTEGER PRIMARY KEY AUTOINCREMENT,
                meaning_id INTEGER NOT NULL,
                example_en TEXT NOT NULL,
                example_vi TEXT,
                FOREIGN KEY(meaning_id) REFERENCES meanings(meaning_id) ON DELETE CASCADE
            )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topic_word (
            topic_id INTEGER,
            word_id INTEGER,
            PRIMARY KEY(topic_id, word_id),
            FOREIGN KEY(topic_id) REFERENCES topics(topic_id),
            FOREIGN KEY(word_id) REFERENCES words(word_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_word_progress (
            user_id INTEGER NOT NULL,
            word_id INTEGER NOT NULL,
            
            -- Cột chính cho SRS
            srs_level INTEGER NOT NULL DEFAULT 0,            -- Cấp độ SRS hiện tại (0, 1, 2, ...)
            next_review_at TEXT NOT NULL,                    -- Thời điểm cần ôn tập lại (dạng 'YYYY-MM-DD HH:MM:SS')
            
            -- Cột thống kê
            correct_streak INTEGER NOT NULL DEFAULT 0,       -- Số lần trả lời đúng liên tiếp
            total_incorrect_count INTEGER NOT NULL DEFAULT 0, -- Tổng số lần trả lời sai
            
            -- Cột trạng thái
            is_mastered INTEGER NOT NULL DEFAULT 0,          -- Đã thành thạo chưa? (0 = chưa, 1 = rồi)
            last_reviewed_at TEXT,                           -- Lần cuối cùng ôn tập
            
            PRIMARY KEY(user_id, word_id),
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY(word_id) REFERENCES words(word_id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_lock (
            user_id INTEGER PRIMARY KEY,
            locked_until TIMESTAMP,
            resend_attempts INTEGER,
            last_resend TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
    """)

    conn.commit()
    conn.close()

    print("Tables created successfully.")

if __name__ == "__main__":
    create_table()