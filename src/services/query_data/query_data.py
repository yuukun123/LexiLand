import sqlite3
import os
import time
from datetime import datetime, timedelta
import random


from src.services.API.word_api import generate_audio_from_text


class QueryData:
    def __init__(self):
        # lấy đường dẫn đến thư mục chứ file hiện tại
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # lùi 1 bước về thư muc services
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
            cursor.execute("SELECT user_id, user_name FROM users WHERE LOWER(user_name) = LOWER(?)", (username,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"Database error in get_user_by_username: {e}")
            return None

    def get_user_id_by_email(self, email):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT user_id FROM users WHERE LOWER(email) = LOWER(?)", (email,))
            row = cursor.fetchone()
            return row[0] if row else None
        except sqlite3.Error as e:
            print(f"Database error in get_user_by_username: {e}")
            return None

    def _find_or_create_word(self, cursor, word_data):
        """
        Hàm helper: Tìm một từ trong CSDL. Nếu không có, tạo mới và trả về word_id.
        Đây là nơi duy nhất xử lý việc INSERT chi tiết.
        """
        word_name = word_data.get('word_name', '')

        cursor.execute(
            "SELECT word_id FROM words WHERE LOWER(word_name) = ?",
            (word_name.lower(),)
        )
        existing_word = cursor.fetchone()

        if existing_word:
            print(f"DEBUG: Từ '{word_name}' đã tồn tại (ID: {existing_word['word_id']}).")
            return existing_word['word_id']
        else:
            print(f"DEBUG: Từ '{word_name}' là từ mới. Đang thêm chi tiết...")

            cursor.execute("INSERT INTO words (word_name) VALUES (?)", (word_name,))
            word_id = cursor.lastrowid

            for pron_info in word_data.get('pronunciations', []):
                cursor.execute("INSERT INTO pronunciations (word_id, region, phonetic_text, audio_url) VALUES (?, ?, ?, ?)",
                               (word_id, pron_info.get('region'), pron_info.get('phonetic_text'), pron_info.get('audio_url')))

            for meaning_info in word_data.get('meanings', []):
                cursor.execute("INSERT INTO meanings (word_id, part_of_speech) VALUES (?, ?)",
                               (word_id, meaning_info.get('part_of_speech')))
                meaning_id = cursor.lastrowid

                if meaning_info.get('definition_en'):
                    cursor.execute("INSERT INTO definition (meaning_id, language, definition_text) VALUES (?, 'en', ?)",
                                   (meaning_id, meaning_info.get('definition_en')))
                if meaning_info.get('definition_vi'):
                    cursor.execute("INSERT INTO definition (meaning_id, language, definition_text) VALUES (?, 'vi', ?)",
                                   (meaning_id, meaning_info.get('definition_vi')))
                if meaning_info.get('example_en'):
                    cursor.execute("INSERT INTO examples (meaning_id, example_en, example_vi) VALUES (?, ?, ?)",
                                   (meaning_id, meaning_info.get('example_en'), meaning_info.get('example_vi')))

            return word_id

    def add_word_to_topic(self, target_topic_id, word_data, user_id):
        """
        Hàm chính: Điều phối việc tìm/tạo từ và sau đó tạo các liên kết.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("BEGIN TRANSACTION")

            has_audio = any(p.get('audio_url') for p in word_data.get('pronunciations', []))

            if not has_audio:
                print(f"DEBUG [DB]: Không có audio cho '{word_data['word_name']}'. Đang tạo TTS...")
                # Tạo file audio
                audio_path = generate_audio_from_text(word_data['word_name'])

                # Tìm và cập nhật bản ghi phiên âm US (nếu có)
                us_pron = next((p for p in word_data['pronunciations'] if p.get('region') == 'US'), None)
                if us_pron:
                    us_pron['audio_url'] = audio_path
                else:
                    # Nếu không có, tạo một bản ghi mới
                    word_data['pronunciations'].append({
                        'region': 'US',
                        'phonetic_text': '',  # Không có text, chỉ có audio
                        'audio_url': audio_path
                    })

            # BƯỚC 1: TÌM HOẶC TẠO TỪ
            word_id = self._find_or_create_word(cursor, word_data)

            if not word_id:
                raise sqlite3.Error("Không thể tìm hoặc tạo word_id.")

            # BƯỚC 2: LUÔN TẠO LIÊN KẾT TOPIC
            cursor.execute(
                "INSERT OR IGNORE INTO topic_word (topic_id, word_id) VALUES (?, ?)",
                (target_topic_id, word_id)
            )
            print(f"DEBUG: Đảm bảo liên kết topic_id={target_topic_id}, word_id={word_id} tồn tại.")

            # BƯỚC 3: LUÔN TẠO BẢN GHI PROGRESS
            now = datetime.now()
            first_review_time = now + timedelta(minutes=10)
            cursor.execute("""
                INSERT OR IGNORE INTO user_word_progress (
                    user_id, word_id, srs_level, next_review_at, last_reviewed_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                           (user_id, word_id, 0, first_review_time.strftime('%Y-%m-%d %H:%M:%S'), now.strftime('%Y-%m-%d %H:%M:%S'))
                           )
            print(f"DEBUG: Đảm bảo bản ghi tiến độ cho user_id={user_id}, word_id={word_id} tồn tại.")

            conn.commit()
            return {"success": True, "word_id": word_id}

        except sqlite3.Error as e:
            if conn: conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            if conn: conn.close()

    def check_word_in_topic(self, topic_id, word_name):
        """
        Kiểm tra xem một từ (dựa trên tên) đã tồn tại trong một chủ đề cụ thể chưa.
        Trả về True nếu đã tồn tại, False nếu chưa.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            # Câu lệnh JOIN để kiểm tra liên kết
            sql_query = """
                SELECT 1 
                FROM topic_word tw
                JOIN words w ON tw.word_id = w.word_id
                WHERE tw.topic_id = ? AND LOWER(w.word_name) = ?
                LIMIT 1
            """
            cursor.execute(sql_query, (topic_id, word_name.lower()))

            # fetchone() sẽ trả về một hàng nếu tìm thấy, hoặc None nếu không
            return cursor.fetchone() is not None
        except sqlite3.Error as e:
            print(f"Database error in check_word_in_topic: {e}")
            return False  # Mặc định là không tồn tại nếu có lỗi
        finally:
            if conn:
                conn.close()

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

    def get_stats_for_topic(self, user_id, topic_id):
        """
        Lấy các chỉ số thống kê (Đã học, Đã nhớ, Cần ôn tập)
        chỉ cho các từ bên trong một chủ đề cụ thể.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            sql_query = """
                SELECT
                    COUNT(p.word_id) as total_learned_in_topic,
                    SUM(CASE WHEN p.is_mastered = 1 THEN 1 ELSE 0 END) as mastered_in_topic,
                    SUM(CASE WHEN p.next_review_at <= ? AND p.is_mastered = 0 THEN 1 ELSE 0 END) as review_needed_in_topic
                FROM
                    user_word_progress p
                JOIN
                    topic_word tw ON p.word_id = tw.word_id
                WHERE
                    p.user_id = ? AND tw.topic_id = ?
            """
            cursor.execute(sql_query, (now_str, user_id, topic_id))

            stats = cursor.fetchone()

            if stats:
                return {
                    "learned": stats["total_learned_in_topic"] or 0,
                    "memorized": stats["mastered_in_topic"] or 0,
                    "review_needed": stats["review_needed_in_topic"] or 0
                }
            else:
                return {"learned": 0, "memorized": 0, "review_needed": 0}

        except sqlite3.Error as e:
            print(f"Database error in get_stats_for_topic: {e}")
            return {"learned": -1, "memorized": -1, "review_needed": -1}
        finally:
            if conn:
                conn.close()

    def get_topic_name_from_topic_id(self, user_id, topic_id):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            sql_query = """
                SELECT
                    t.topic_name
                FROM
                    topics t
                JOIN
                    users u ON u.user_id = t.user_id
                WHERE
                    u.user_id = ? AND t.topic_id = ?
            """
            cursor.execute(sql_query, (user_id, topic_id))

            result_row = cursor.fetchone()

            if result_row:
                return result_row['topic_name']
            else:
                return None

        except sqlite3.Error as e:
            print(f"Database error in get_stats_for_topic: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_words_in_topic(self, topic_id):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            # Câu lệnh này sẽ lấy TẤT CẢ thông tin cần thiết
            sql_query = """
                SELECT
                    w.word_id,
                    w.word_name,
                    -- Lấy định nghĩa tiếng Việt đầu tiên tìm thấy
                    (SELECT def.definition_text FROM definition def JOIN meanings m ON def.meaning_id = m.meaning_id WHERE m.word_id = w.word_id AND def.language = 'vi' LIMIT 1) as definition_vi,
                    -- Lấy ví dụ tiếng Anh đầu tiên tìm thấy
                    (SELECT ex.example_en FROM examples ex JOIN meanings m ON ex.meaning_id = m.meaning_id WHERE m.word_id = w.word_id LIMIT 1) as example_en
                FROM
                    topic_word tw
                JOIN
                    words w ON tw.word_id = w.word_id
                WHERE
                    tw.topic_id = ?
                ORDER BY
                    w.word_name ASC
            """
            cursor.execute(sql_query, (topic_id,))
            words = [dict(row) for row in cursor.fetchall()]

            # Bây giờ, lặp qua từng từ để lấy tất cả các cách phát âm của nó
            for word in words:
                cursor.execute(
                    "SELECT region, phonetic_text, audio_url FROM pronunciations WHERE word_id = ?",
                    (word['word_id'],)
                )
                word['pronunciations'] = [dict(row) for row in cursor.fetchall()]

            return words
        except sqlite3.Error as e:
            print(f"Database error in get_words_in_topic: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def add_topic(self, user_id, topic_name):
        """
        Thêm một chủ đề mới cho một người dùng.
        Xử lý trường hợp tên chủ đề đã tồn tại.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # UNIQUE(topic_name, user_id) trong CSDL sẽ tự động ngăn trùng lặp
            # và ném ra lỗi IntegrityError.

            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            cursor.execute(
                "INSERT INTO topics (topic_name, user_id, created_at) VALUES (?, ?, ?)",
                (topic_name, user_id, now_str)
            )

            new_topic_id = cursor.lastrowid
            conn.commit()

            print(f"DEBUG: Đã tạo topic mới '{topic_name}' với ID: {new_topic_id}")
            return {"success": True, "topic_id": new_topic_id}

        except sqlite3.IntegrityError:
            # Lỗi này xảy ra do ràng buộc UNIQUE(topic_name, user_id)
            print(f"CẢNH BÁO: Topic '{topic_name}' đã tồn tại cho user_id={user_id}.")
            # Chúng ta có thể chọn lấy ID của topic đã tồn tại
            cursor.execute(
                "SELECT topic_id FROM topics WHERE user_id = ? AND topic_name = ?",
                (user_id, topic_name)
            )
            existing_topic = cursor.fetchone()
            if existing_topic:
                return {"success": True, "topic_id": existing_topic['topic_id'], "message": "Topic already exists."}
            else:
                # Trường hợp hiếm gặp
                return {"success": False, "error": "Topic already exists but could not be retrieved."}

        except sqlite3.Error as e:
            if conn: conn.rollback()
            print(f"Lỗi CSDL khi thêm topic: {e}")
            return {"success": False, "error": str(e)}
        finally:
            if conn:
                conn.close()

    def update_word_details(self, word_id, word_data):
        """Cập nhật thông tin chi tiết của một từ đã có."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("BEGIN TRANSACTION")

            # Cập nhật bảng words
            cursor.execute(
                "UPDATE words SET word_name = ? WHERE word_id = ?",
                # SỬA LỖI: Bỏ dấu phẩy thừa
                (word_data.get('word_name'), word_id)
            )

            # Xóa các chi tiết cũ để thêm lại
            # (PRAGMA foreign_keys = ON sẽ đảm bảo definition/examples bị xóa theo meanings)
            cursor.execute("DELETE FROM pronunciations WHERE word_id = ?", (word_id,))
            cursor.execute("DELETE FROM meanings WHERE word_id = ?", (word_id,))

            # Thêm lại pronunciations một cách an toàn
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

            # Thêm lại meanings và các chi tiết liên quan một cách an toàn
            for meaning_info in word_data.get('meanings', []):
                cursor.execute(
                    "INSERT INTO meanings (word_id, part_of_speech) VALUES (?, ?)",
                    (word_id, meaning_info.get('part_of_speech', 'N/A'))
                )
                meaning_id = cursor.lastrowid

                if meaning_info.get('definition_en'):
                    cursor.execute(
                        "INSERT INTO definition (meaning_id, language, definition_text) VALUES (?, 'en', ?)",
                        (meaning_id, meaning_info.get('definition_en'))
                    )
                if meaning_info.get('definition_vi'):
                    cursor.execute(
                        "INSERT INTO definition (meaning_id, language, definition_text) VALUES (?, 'vi', ?)",
                        (meaning_id, meaning_info.get('definition_vi'))
                    )
                if meaning_info.get('example_en'):
                    cursor.execute(
                        "INSERT INTO examples (meaning_id, example_en, example_vi) VALUES (?, ?, ?)",
                        (
                            meaning_id,
                            meaning_info.get('example_en'),
                            meaning_info.get('example_vi')
                        )
                    )

            conn.commit()
            return {"success": True}

        except sqlite3.Error as e:
            if conn: conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            if conn: conn.close()

    def get_full_word_details(self, word_id):
        """
        Lấy TẤT CẢ thông tin chi tiết của một từ duy nhất bằng word_id.
        Hàm này sẽ trả về một dictionary có cấu trúc phức tạp, sẵn sàng
        để điền vào form hoặc để xử lý tiếp.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # --- 1. Lấy thông tin cơ bản của từ ---
            cursor.execute("SELECT word_id, word_name FROM words WHERE word_id = ?", (word_id,))
            word_base = cursor.fetchone()

            if not word_base:
                return None  # Trả về None nếu không tìm thấy từ

            # Khởi tạo dictionary kết quả
            word_details = dict(word_base)

            # --- 2. Lấy tất cả các cách phát âm ---
            cursor.execute("SELECT region, phonetic_text, audio_url FROM pronunciations WHERE word_id = ?", (word_id,))
            word_details['pronunciations'] = [dict(row) for row in cursor.fetchall()]

            # --- 3. Lấy tất cả các nghĩa (và chi tiết của chúng) ---
            cursor.execute("SELECT meaning_id, part_of_speech FROM meanings WHERE word_id = ?", (word_id,))
            meanings_rows = cursor.fetchall()

            word_details['meanings'] = []
            for meaning_row in meanings_rows:
                meaning_info = dict(meaning_row)
                meaning_id = meaning_info['meaning_id']

                # 3.1 Lấy các định nghĩa cho nghĩa này
                cursor.execute("SELECT language, definition_text FROM definition WHERE meaning_id = ?", (meaning_id,))
                definitions = cursor.fetchall()
                for d in definitions:
                    if d['language'] == 'en':
                        meaning_info['definition_en'] = d['definition_text']
                    elif d['language'] == 'vi':
                        meaning_info['definition_vi'] = d['definition_text']

                # 3.2 Lấy các ví dụ cho nghĩa này
                cursor.execute("SELECT example_en, example_vi FROM examples WHERE meaning_id = ?", (meaning_id,))
                examples = cursor.fetchall()
                # Tạm thời chỉ lấy ví dụ đầu tiên, bạn có thể sửa để lấy tất cả
                if examples:
                    meaning_info['example_en'] = examples[0]['example_en']
                    meaning_info['example_vi'] = examples[0]['example_vi']

                word_details['meanings'].append(meaning_info)

            return word_details

        except sqlite3.Error as e:
            print(f"Database error in get_full_word_details for word_id={word_id}: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def remove_word_from_topic(self, topic_id, word_id):
        """
        Xóa liên kết giữa một từ và một chủ đề trong bảng topic_word.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM topic_word WHERE topic_id = ? AND word_id = ?",
                (topic_id, word_id)
            )
            conn.commit()

            # rowcount > 0 có nghĩa là đã có ít nhất 1 hàng bị xóa
            if cursor.rowcount > 0:
                print(f"INFO: Đã xóa thành công liên kết giữa topic_id={topic_id} và word_id={word_id}")
                return {"success": True}
            else:
                print(f"CẢNH BÁO: Không tìm thấy liên kết để xóa cho topic_id={topic_id}, word_id={word_id}")
                return {"success": False, "error": "Link not found"}

        except sqlite3.Error as e:
            if conn: conn.rollback()
            print(f"LỖI CSDL khi xóa liên kết từ/chủ đề: {e}")
            return {"success": False, "error": str(e)}
        finally:
            if conn:
                conn.close()

    # def remove_word_from_topic(self, topic_id, word_id):
    #     """
    #     Xóa liên kết từ/chủ đề. Nếu từ trở thành "mồ côi", xóa nó
    #     và TRẢ VỀ danh sách các file audio cần được dọn dẹp.
    #     """
    #     conn = self._get_connection()
    #     try:
    #         cursor = conn.cursor()
    #         cursor.execute("BEGIN TRANSACTION")
    #
    #         # Xóa liên kết
    #         cursor.execute(
    #             "DELETE FROM topic_word WHERE topic_id = ? AND word_id = ?",
    #             (topic_id, word_id)
    #         )
    #         if cursor.rowcount == 0:
    #             conn.rollback();
    #             return {"success": False, "error": "Link not found"}
    #
    #         # Kiểm tra từ "mồ côi"
    #         cursor.execute("SELECT COUNT(*) FROM topic_word WHERE word_id = ?", (word_id,))
    #         remaining_links = cursor.fetchone()[0]
    #
    #         audio_files_to_delete = []  # Danh sách để trả về
    #
    #         if remaining_links == 0:
    #             print(f"INFO: Từ word_id={word_id} đã trở thành 'mồ côi'. Chuẩn bị xóa.")
    #
    #             # BƯỚC MỚI: Lấy danh sách audio_url TRƯỚC KHI XÓA
    #             cursor.execute(
    #                 "SELECT audio_url FROM pronunciations WHERE word_id = ?",
    #                 (word_id,)
    #             )
    #             results = cursor.fetchall()
    #             # Chỉ thêm các đường dẫn file cục bộ, bỏ qua các URL http
    #             audio_files_to_delete = [row['audio_url'] for row in results if row['audio_url'] and not row['audio_url'].startswith('http')]
    #
    #             # Bây giờ mới thực hiện xóa
    #             # ON DELETE CASCADE sẽ tự động xóa pronunciations, meanings, etc.
    #             cursor.execute("DELETE FROM words WHERE word_id = ?", (word_id,))
    #
    #             # Cũng xóa khỏi bảng progress
    #             cursor.execute("DELETE FROM user_word_progress WHERE word_id = ?", (word_id,))
    #
    #             print(f"INFO: Đã xóa hoàn toàn word_id={word_id}. Các file cần dọn dẹp: {audio_files_to_delete}")
    #
    #         conn.commit()
    #         # Trả về thành công và danh sách file cần xóa
    #         return {"success": True, "deleted_audio_files": audio_files_to_delete}
    #
    #     except sqlite3.Error as e:
    #         if conn: conn.rollback()
    #         return {"success": False, "error": str(e)}
    #     finally:
    #         if conn: conn.close()

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

    def get_list_topic(self, user_id):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
            """
                SELECT T.topic_id, T.topic_name, COUNT(TW.word_id) AS word_count
                FROM topics AS T
                LEFT JOIN topic_word AS TW ON T.topic_id = TW.topic_id
                WHERE T.user_id = ?
                GROUP BY T.topic_id, T.topic_name;

            """,(user_id,)
            )
            rows = cursor.fetchall()
            topics = [dict(row) for row in rows]
            return topics
        except Exception as e:
            print(f"\n!!! ĐÃ XẢY RA LỖI KHI DEBUG: {e}")
        finally:
            if conn:
                conn.close()
    def get_name_topic_by_id(self,user_id, topic_id):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            placeholders = ",".join(["?"] * len(topic_id))
            cursor.execute(
            f"""
                SELECT topic_id, topic_name FROM topics
                WHERE user_id = ? AND topic_id IN ({placeholders})
            """,(user_id, *topic_id)
            )
            rows = cursor.fetchall()
            return [{"id": row[0], "name": row[1]} for row in rows]
        except Exception as e:
            print(f"\n!!! ĐÃ XẢY RA LỖI KHI DEBUG: {e}")
        finally:
            if conn:
                conn.close()

    def get_list_words_for_practice(self,user_id, topic_ids):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            if not topic_ids:
                return []
            placeholders = ",".join(["?"] * len(topic_ids))
            cursor.execute(
            f"""
                SELECT 
                    w.word_id,
                    w.word_name,
                    uwp.correct_streak,
                    uwp.total_incorrect_count,
                    uwp.next_review_at,
	                uwp.is_mastered,
	                uwp.srs_level,
	                d.definition_text,
	                m.part_of_speech
                FROM words AS w
                JOIN meanings AS m on m.word_id = w.word_id 
                JOIN definition AS d on d.meaning_id = m.meaning_id
                JOIN topic_word AS tw ON tw.word_id = w.word_id
                JOIN topics AS t ON tw.topic_id = t.topic_id
                JOIN user_word_progress AS uwp ON uwp.word_id = w.word_id
                WHERE uwp.user_id = ?
                AND d.language = 'vi'
                AND t.topic_id IN ({placeholders})
                ORDER BY uwp.total_incorrect_count DESC,
                uwp.correct_streak ASC, srs_level ASC;
            """,(user_id, *topic_ids)
            )
            rows = cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "correct_streak": row[2],
                    "total_incorrect_count": row[3],
                    "next_review_at": row[4],
                    "is_mastered": row[5],
                    "srs_level": row[6],
                    "definition_text": row[7],
                    "part_of_speech": row[8]
                }
                for row in rows
            ]
        except Exception as e:
            print(f"\n!!! ĐÃ XẢY RA LỖI KHI DEBUG: {e}")
        finally:
            if conn:
                conn.close()

    def get_wrong_definitions(self, word_id, correct_definition, num_wrong = 3):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
            """
            SELECT d.definition_text
            FROM meanings AS m
            JOIN definition AS d ON d.meaning_id = m.meaning_id
            WHERE m.word_id != ?
              AND d.language = 'vi'
              AND d.definition_text != ?
            """,
            (word_id, correct_definition)
            )
            rows = cursor.fetchall()
            wrong_defs = [row[0] for row in rows]
            if len(wrong_defs) > num_wrong:
                wrong_defs = random.sample(wrong_defs, num_wrong)
            return wrong_defs
        except Exception as e:
            print(f"\n!!! LỖI KHI LẤY NGHĨA SAI: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def update_word_stats(self,data: dict):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
            """
            UPDATE user_word_progress
            SET srs_level = :srs_level,
                correct_streak = :correct_streak,
                total_incorrect_count = :total_incorrect_count,
                is_mastered = :is_mastered,
                last_reviewed_at = :last_reviewed_at,
                next_review_at = :next_review_at
                WHERE user_id = :user_id AND word_id = :word_id
            """, {**data}
            )
            conn.commit()
        except Exception as e:
            print(f"\n!!! LỖI KHI LẤY NGHĨA SAI: {e}")
            return []
        finally:
            if conn:
                conn.close()
    def check_email_exist(self,email):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id FROM users WHERE email = ?", (email,)
            )
            user = cursor.fetchone()
            return user is not None
        except Exception as e:
            print(f"\n!!! LỖI KHI LẤY NGHĨA SAI: {e}")
            return []
        finally:
            if conn:
                conn.close()
    def update_new_password(self, password_hash, email):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE users
                SET password = :password_hash
                WHERE email = :email
                """,
                {"password_hash": password_hash, "email": email}
            )
            conn.commit()
        except Exception as e:
            print(f"\n!!! LỖI KHI UPDATE PASSWORD: {e}")
            return False
        finally:
            if conn:
                conn.close()
        return True
    def get_hashed_password(self, email):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT password FROM users WHERE email = ?", (email,)
            )
            password = cursor.fetchone()
            if password:
                return password[0]
            return None
        except Exception as e:
            print(f"\n!!! LỖI KHI LẤY PASS SAI: {e}")
            return []
        finally:
            if conn:
                conn.close()
    # --- LOCK ---
    def get_locked_until(self, user_id):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT locked_until FROM user_lock WHERE user_id = ?", (user_id,)
            )
            rows = cursor.fetchone()
            if rows:
                return rows[0]
            return None
        except Exception as e:
            print(f"\n!!! LỖI KHI LẤY lock_user SAI: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def lock_user(self,user_id, lock_time_second):
        locked_until = int(time.time()) + lock_time_second
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            # cursor.execute(
            #     """
            #     INSERT INTO user_lock (user_id, locked_until, resend_attempts, last_resend)
            #     VALUES (?, ?, 0, NULL)
            #     ON CONFLICT(user_id) DO UPDATE SET locked_until=excluded.locked_until
            #     """, (user_id, locked_until)
            # )
            cursor.execute(
                """
                INSERT INTO user_lock (user_id, locked_until)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    locked_until=excluded.locked_until
                """, (user_id, locked_until)
            )
            conn.commit()
        except Exception as e:
            print(f"\n!!! LỖI KHI LẤY lock_user SAI: {e}")
            return []
        finally:
            if conn:
                conn.close()
    def get_resend_info(self, user_id):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT resend_attempts, last_resend FROM user_lock WHERE user_id = ?", (user_id,)
            )
            rows = cursor.fetchone()
            if rows:
                return rows[0], rows[1]
            return 0, None
        except Exception as e:
            print(f"\n!!! LỖI KHI LẤY resend SAI: {e}")
            return []
        finally:
            if conn:
                conn.close()
    # --- RESEND ---
    def update_resend(self, user_id, attempts, now):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE user_lock SET resend_attempts=?, last_resend=? WHERE user_id=?", (attempts, now, user_id)
            )
            conn.commit()
        except Exception as e:
            print(f"\n!!! LỖI KHI LẤY lock_user SAI: {e}")
            return []
        finally:
            if conn:
                conn.close()

    # def insert_resend(self, user_id, now):
    #     conn = self._get_connection()
    #     try:
    #         cursor = conn.cursor()
    #         cursor.execute(
    #             """
    #             INSERT INTO user_lock (user_id, resend_attempts, last_resend, locked_until)
    #             VALUES (?, ?, ?, NULL)
    #             ON CONFLICT(user_id) DO UPDATE SET locked_until=excluded.locked_until
    #             """, (user_id, 1, now)
    #         )
    #         conn.commit()
    #     except Exception as e:
    #         print(f"\n!!! LỖI KHI LẤY lock_user SAI: {e}")
    #         return []
    #     finally:
    #         if conn:
    #             conn.close()

    def insert_resend(self, user_id, now):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO user_lock (user_id, resend_attempts, last_resend)
                VALUES (?, 1, ?)  -- Giả sử lần đầu luôn là 1 attempt
                ON CONFLICT(user_id) DO UPDATE SET
                    resend_attempts=1,          -- Reset lại attempts
                    last_resend=excluded.last_resend  -- Cập nhật thời gian
                """, (user_id, now)
            )
            conn.commit()
        except Exception as e:
            print(f"\n!!! LỖI KHI LẤY lock_user SAI: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_user_status(self, user_id):
        """
        Lấy tất cả thông tin trạng thái của người dùng: attempts, last_resend, locked_until.
        Đây là hàm thay thế cho get_resend_info.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT resend_attempts, last_resend, locked_until FROM user_lock WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            if row:
                return row[0], row[1], row[2]  # attempts, last_resend, locked_until

            # Nếu người dùng chưa tồn tại trong bảng, trả về trạng thái mặc định ban đầu
            return None, None, None  # Sử dụng None để dễ dàng kiểm tra user mới

        except Exception as e:
            print(f"\n!!! LỖI KHI LẤY get_user_status: {e}")
            # Trong trường hợp lỗi, trả về trạng thái an toàn (coi như user mới)
            return None, None, None
        finally:
            if conn:
                conn.close()

    def upsert_resend_info(self, user_id, attempts, now):
        """
        Hàm gộp: Vừa có thể insert người dùng mới, vừa có thể update người dùng cũ.
        Hàm này an toàn hơn vì nó không ảnh hưởng đến cột locked_until.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO user_lock (user_id, resend_attempts, last_resend)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    resend_attempts = excluded.resend_attempts,
                    last_resend = excluded.last_resend
                """,
                (user_id, attempts, now)
            )
            conn.commit()
        except Exception as e:
            print(f"\n!!! LỖI KHI upsert_resend_info: {e}")
        finally:
            if conn:
                conn.close()
# if __name__ == "__main__":
#     query = QueryData()
#     query.remove_word_from_topic(self, )

