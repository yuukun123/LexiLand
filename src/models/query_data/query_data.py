import sqlite3
import os
from datetime import datetime


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
        os.makedirs(db_folder, exist_ok=True)
        # Và cuối cùng, đường dẫn đầy đủ đến file CSDL
        self.db_path = os.path.join(db_folder, "database.db")
        print(f"DEBUG: QueryData initialized. DB path is '{self.db_path}'")

    def _get_connection(self):
        """Hàm tiện ích để tạo một kết nối mới."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_user_by_username(self, username):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT user_id, user_name FROM users WHERE user_name = ?", (username,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"Database error in get_user_by_username: {e}")
            return None

    def add_word_to_topic(self, target_topic_id, word_data, user_id=None):
        """
        Lưu một từ mới hoàn chỉnh (bao gồm cả pronunciations)
        và liên kết nó với một chủ đề.

        word_data format:
        {
            'word_name': 'example',
            'pronunciations': [
                {'phonetic_text': '/ɪɡˈzæmpəl/', 'audio_url': '.../us.mp3', 'region': 'US'}
            ],
            'meanings': [
                {
                    'part_of_speech': 'noun',
                    'definition_en': '...', 'definition_vi': '...',
                    'example_en': '...', 'example_vi': '...'
                }
            ]
        }
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("BEGIN TRANSACTION")

            # --- BƯỚC 1: XỬ LÝ BẢNG `words` ---
            cursor.execute("SELECT word_id FROM words WHERE word_name = ?", (word_data['word_name'],))
            existing_word = cursor.fetchone()

            if existing_word:
                word_id = existing_word['word_id']
                print(f"DEBUG: Từ '{word_data['word_name']}' đã tồn tại (ID: {word_id}).")
            else:
                print(f"DEBUG: Từ '{word_data['word_name']}' là từ mới. Bắt đầu thêm chi tiết.")

                # 1.1 Thêm vào bảng `words` (không còn phonetic)
                cursor.execute(
                    "INSERT INTO words (word_name) VALUES (?)",
                    (word_data['word_name'],)
                )
                word_id = cursor.lastrowid

                # 1.2 THÊM MỚI: Thêm tất cả pronunciations
                for pron_info in word_data.get('pronunciations', []):
                    cursor.execute(
                        "INSERT INTO pronunciations (word_id, region, phonetic_text, audio_url) VALUES (?, ?, ?, ?)",
                        (
                            word_id,
                            pron_info.get('region'),
                            pron_info.get('phonetic_text'),
                            pron_info.get('audio_url')
                        )
                    )

                # 1.3 Thêm tất cả meanings, definitions, examples (giữ nguyên logic)
                for meaning_info in word_data.get('meanings', []):
                    cursor.execute(
                        "INSERT INTO meanings (word_id, part_of_speech) VALUES (?, ?)",
                        (word_id, meaning_info['part_of_speech'])
                    )
                    meaning_id = cursor.lastrowid

                    if 'definition_en' in meaning_info:
                        cursor.execute(
                            "INSERT INTO definition (meaning_id, language, definition_text) VALUES (?, 'en', ?)",
                            (meaning_id, meaning_info['definition_en'])
                        )
                    if 'definition_vi' in meaning_info:
                        cursor.execute(
                            "INSERT INTO definition (meaning_id, language, definition_text) VALUES (?, 'vi', ?)",
                            (meaning_id, meaning_info['definition_vi'])
                        )
                    if 'example_en' in meaning_info:
                        cursor.execute(
                            "INSERT INTO examples (meaning_id, example_en, example_vi) VALUES (?, ?, ?)",
                            (meaning_id, meaning_info['example_en'], meaning_info.get('example_vi'))
                        )

            # --- BƯỚC 2: LUÔN TẠO LIÊN KẾT `topic_word` ---
            cursor.execute(
                "INSERT OR IGNORE INTO topic_word (topic_id, word_id) VALUES (?, ?)",
                (target_topic_id, word_id)
            )
            print(f"DEBUG: Đảm bảo liên kết giữa topic_id={target_topic_id} và word_id={word_id} tồn tại.")

            # Tính thời gian ôn tập đầu tiên (ví dụ: 10 phút sau)
            first_review_time = datetime.now() + timedelta(minutes=10)
            first_review_str = first_review_time.strftime('%Y-%m-%d %H:%M:%S')

            # Dùng INSERT OR IGNORE: Chỉ chèn nếu cặp (user_id, word_id) chưa tồn tại.
            # Điều này ngăn việc reset tiến độ của một từ đã học.
            cursor.execute("""
                INSERT OR IGNORE INTO user_word_progress (
                    user_id, 
                    word_id, 
                    srs_level, 
                    next_review_at,
                    last_reviewed_at
                ) VALUES (?, ?, 0, ?, ?)
                """,
                           (user_id, word_id, first_review_str, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                           )
            print(f"DEBUG: Đảm bảo bản ghi tiến độ cho user_id={user_id} và word_id={word_id} tồn tại.")

            conn.commit()
            print("INFO: Giao dịch thành công. Từ và tiến độ ban đầu đã được lưu.")
            return {"success": True, "word_id": word_id}

        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            print(f"LỖI CSDL: Giao dịch thất bại. Đã hoàn tác. Lỗi: {e}")
            return {"success": False, "error": str(e)}

        finally:
            if conn:
                conn.close()
                print(f"DEBUG: Kết nối CSDL đã được đóng.")

    def get_all_topics_with_word_count(self, user_id):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            sql_query = """
                SELECT 
                    t.topic_id, 
                    t.topic_name,
                    t.created_at,
                    COUNT(tw.word_id) as word_count
                FROM 
                    topics t
                LEFT JOIN 
                    topic_word tw ON t.topic_id = tw.topic_id
                WHERE 
                    t.user_id = ?
                GROUP BY 
                    t.topic_id, t.topic_name, t.created_at
                ORDER BY 
                    CASE WHEN t.topic_name = 'Other' THEN 0 ELSE 1 END, 
                    t.created_at DESC
            """

            cursor.execute(sql_query, (user_id,))
            rows = [dict(row) for row in cursor.fetchall()]

            print(f"DEBUG (NEW QUERY): Kết quả đếm từ cho user_id={user_id}: {rows}")

            return rows

        except sqlite3.Error as e:
            print(f"Database error in get_all_topics_with_word_count: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_user_stats(self, user_id):
        """
        Lấy tất cả các chỉ số thống kê (Đã học, Đã nhớ, Cần ôn tập)
        cho một người dùng trong một lần truy vấn duy nhất.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # Lấy thời gian hiện tại để so sánh
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            sql_query = """
                SELECT
                    COUNT(word_id) as total_learned,
                    SUM(CASE WHEN is_mastered = 1 THEN 1 ELSE 0 END) as memorized,
                    SUM(CASE WHEN next_review_at <= ? AND is_mastered = 0 THEN 1 ELSE 0 END) as review_needed
                FROM
                    user_word_progress
                WHERE
                    user_id = ?
            """
            cursor.execute(sql_query, (now_str, user_id))

            stats = cursor.fetchone()

            if stats:
                # Trả về một dictionary, với giá trị mặc định là 0 nếu NULL
                return {
                    "learned": stats["total_learned"] or 0,
                    "memorized": stats["memorized"] or 0,
                    "review_needed": stats["review_needed"] or 0
                }
            else:
                # Nếu người dùng chưa học từ nào
                return {"learned": 0, "memorized": 0, "review_needed": 0}

        except sqlite3.Error as e:
            print(f"Database error in get_user_stats: {e}")
            return {"learned": -1, "memorized": -1, "review_needed": -1}  # Trả về -1 để báo lỗi
        finally:
            if conn:
                conn.close()

    def debug_user_data(self, user_id):
        """
        In ra một báo cáo chi tiết về dữ liệu của một người dùng để gỡ lỗi.
        """
        conn = self._get_connection()
        print("\n" + "=" * 20 + f" BÁO CÁO DEBUG CHO USER ID: {user_id} " + "=" * 20)
        try:
            cursor = conn.cursor()

            # 1. Thông tin người dùng
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user_info = cursor.fetchone()
            print(f"\n[1] THÔNG TIN USER:")
            print(dict(user_info) if user_info else "==> KHÔNG TÌM THẤY USER NÀY!")

            # 2. Các chủ đề của người dùng này
            cursor.execute("SELECT * FROM topics WHERE user_id = ?", (user_id,))
            topics = [dict(row) for row in cursor.fetchall()]
            print(f"\n[2] CÁC CHỦ ĐỀ CỦA USER NÀY ({len(topics)} chủ đề):")
            if topics:
                for topic in topics:
                    print(f"  - Topic ID: {topic['topic_id']}, Tên: '{topic['topic_name']}'")
            else:
                print("==> USER NÀY KHÔNG CÓ CHỦ ĐỀ NÀO.")

            # 3. Các từ được liên kết với các chủ đề của người dùng này
            print(f"\n[3] CÁC TỪ TRONG CÁC CHỦ ĐỀ TRÊN:")
            topic_ids = [t['topic_id'] for t in topics]
            if topic_ids:
                # Dùng IN (...) để truy vấn tất cả các topic ID cùng lúc
                placeholders = ','.join(['?'] * len(topic_ids))
                sql = f"""
                    SELECT tw.topic_id, tw.word_id, w.word_name
                    FROM topic_word tw
                    JOIN words w ON tw.word_id = w.word_id
                    WHERE tw.topic_id IN ({placeholders})
                """
                cursor.execute(sql, topic_ids)
                topic_words = [dict(row) for row in cursor.fetchall()]

                if topic_words:
                    for tw in topic_words:
                        print(f"  - Topic ID {tw['topic_id']} chứa Word ID {tw['word_id']} ('{tw['word_name']}')")
                else:
                    print("==> CÁC CHỦ ĐỀ TRÊN CHƯA CÓ TỪ NÀO.")
            else:
                print("==> BỎ QUA VÌ KHÔNG CÓ CHỦ ĐỀ.")

            # 4. In lại kết quả của hàm đếm từ (để so sánh)
            print(f"\n[4] KẾT QUẢ TỪ HÀM get_all_topics_with_word_count:")
            counted_topics = self.get_all_topics_with_word_count(user_id)  # Gọi lại hàm gốc
            print(counted_topics)

        except Exception as e:
            print(f"\n!!! ĐÃ XẢY RA LỖI KHI DEBUG: {e}")
        finally:
            if conn:
                conn.close()
        print("=" * 20 + " KẾT THÚC BÁO CÁO " + "=" * 20 + "\n")