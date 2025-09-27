import asyncio
import requests
import urllib.parse # thư viện xử lý url
import re
import google.generativeai as genai
import os
import aiohttp
from gtts import gTTS
import json

api_cache = {}

# CÁCH ĐÚNG ĐỂ LẤY VÀ CẤU HÌNH API KEY
try:
    # Cách tốt nhất: Lấy key từ biến môi trường
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    if not GOOGLE_API_KEY:
        # Nếu không có biến môi trường, dùng key bạn hardcode (chỉ để test)
        print("Khoông tìm thấy biến môi trường. Dùng key hardcode.")
        GOOGLE_API_KEY = "AIzaSyBTlhhYZkFdzwmUBSsN98dpUC9X6pSO8Wg" # <--- THAY BẰNG KEY THẬT CỦA BẠN
    genai.configure(api_key=GOOGLE_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-2.0-flash')
    print(">>> Cáu hình Gemini API Key thanh cong!")
except Exception as e:
    print(f"Lỗi cấu hình Gemini API Key: {e}. Hãy chắc chắn bạn đã đặt biến môi trường hoặc điền key vào code.")
    exit()

def check_multi_word_phrase(text):
    return ' ' in text.strip()

async def get_dictionary_data_async(session, word):
    """
    Gọi API của Wiktionary và chuyển đổi kết quả về định dạng giống
    như DictionaryAPI.dev để xử lý nhất quán.
    """
    url = f'https://api.dictionaryapi.dev/api/v2/entries/en/{word}'
    try:
        async with session.get(url, timeout=5) as response:
            if response.status == 200:
                print(">>> DictionaryAPI.dev thành công!")
                return await response.json()
    except asyncio.TimeoutError:
        print("--- DictionaryAPI.dev timeout.")
    except Exception:
        pass

    url_wiktionary = f'https://en.wiktionary.org/api/rest_v1/page/definition/{word}'
    try:
        async with session.get(url_wiktionary, timeout = 5) as response:
            if response.status == 200:
                wiktionary_data = await response.json()

                # --- Bắt đầu sơ chế (transform) ---
                if 'en' in wiktionary_data and wiktionary_data['en']:
                    print(">>> Wiktionary API successful")

                # Tạo ra một "khay nguyên liệu" mới theo đúng tiêu chuẩn
                formatted_entry = {"word": word, "phonetic": "", "meanings": []}

                for pos_data in wiktionary_data['en']:
                    meaning = {"partOfSpeech": pos_data.get('partOfSpeech', 'N/A'), "definitions": []}
                    for def_item in pos_data.get('definitions', []):
                        clean_definition = re.sub('<[^<]+?>', '', def_item.get('definition', ''))
                        definition_info = {"definition": clean_definition}
                        if 'examples' in def_item and def_item['examples']:
                            clean_example = re.sub('<[^<]+?>', '', def_item['examples'][0])
                            definition_info['example'] = clean_example
                        meaning['definitions'].append(definition_info)
                    formatted_entry['meanings'].append(meaning)
                # Trả về khay nguyên liệu đã được sơ chế hoàn hảo
                return [formatted_entry]
    except Exception:
        pass

    print("--Both appi connect fail")
    return None

async def prompt_gemini_async(word_to_define):
    """
    Gọi API của Gemini và chuyển đổi kết quả về định dạng giống
    như DictionaryAPI.dev để xử lý nhất quán.
    """
    if check_multi_word_phrase(word_to_define):
        prompt_header = f"""
        Chỉ cần giải thích cụm từ hoặc thành ngữ và tối đa 11 từ không cần ghi thêm bất cứ từ gì hay câu gì không liên quan
        Giải thích từ "{word_to_define}" bằng tiếng Anh và tiếng việt một cách thật đơn giản cho người mới học một cách dễ hiểu, tính liên quan, ngữ cảnh thực tế và khả năng ghi nhớ và không dùng định nghĩa trong từ điển
        Thêm phiên âm Uk
        Thêm phiên âm US
        Thêm loại từ cho cụm từ hoặc thành ngữ không cần tiếng việt
        Thêm phần dịch nghĩa tiếng việt cho ví dụ
        Sau đó, cung cấp 1 câu ví dụ rất phổ biến và tự nhiên trong giao tiếp hàng ngày.
        """

    else:
        prompt_header = f"""
        cho tôi nghĩa tiếng việt của từ {word_to_define}, Thêm phiên âm UK và US.
        cho tôi 2 câu ví dụ cả tiếng anh và tiếng việt của từ {word_to_define}
        chỉ cho nghĩa không cần giải thích cụ thể nó là gì
        """

    prompt_footer = f"""
        Định dạng đầu ra phải như sau:
        Phonetic UK: [phiên âm UK]
        Phonetic US: [phiên âm US]
        Part of speech: [loại từ]
        Simple Definition English : [định nghĩa tiếng anh của bạn ở đây]
        Simple Definition Vietnamese : [định nghĩa tiếng việt của bạn ở đây]
        Common Examples :
        -[câu ví dụ] ([câu việt dụ])
    """
    full_prompt = prompt_header + prompt_footer
    # --- Gửi yêu cầu đến Gemini và nhận kết quả ---
    try:
        response = await gemini_model.generate_content_async(full_prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Đã xảy ra lỗi khi gọi API: {e}")
        return None

async def check_spelling_with_gemini(word_to_check):
    """
    Sử dụng Gemini để kiểm tra chính tả và đưa ra gợi ý.
    Trả về một dictionary JSON.
    """
    print(f"DEBUG: Bắt đầu kiểm tra chính tả cho '{word_to_check}'...")

    prompt = f"""
    Analyze the English word "{word_to_check}". 
    Check if it is spelled correctly. 
    If it is spelled incorrectly, provide the correct spelling.
    Respond ONLY with a valid JSON object in the following format, with no other text or markdown:
    {{
      "is_correct": boolean,
      "suggestion": "string"
    }}
    If the word is correct, "suggestion" should be an empty string.
    """

    try:
        response = await gemini_model.generate_content_async(prompt)

        # Làm sạch và phân tích JSON
        clean_json_str = response.text.strip().replace("```json", "").replace("```", "").strip()
        result = json.loads(clean_json_str)

        print(f"DEBUG: Kết quả kiểm tra chính tả: {result}")
        return result

    except (json.JSONDecodeError, Exception) as e:
        print(f"Lỗi khi kiểm tra chính tả với Gemini: {e}")
        # Mặc định là đúng nếu có lỗi API
        return {"is_correct": True, "suggestion": ""}

async def extract_pos_from_data(session, dict_data):
    if not dict_data or not isinstance(dict_data, list) or not dict_data[0].get('meanings'):
        return [], "N/A", "(Not found in dictionary)"

    try:
        pronunciations = []
        if dict_data[0].get('phonetics'):
            for p in dict_data[0]['phonetics']:
                pronunciations.append({
                    "region": "US" if "us.mp3" in p.get('audio', '') else "UK" if "uk.mp3" in p.get('audio', '') else "Dict",
                    "phonetic_text": p.get('text', ''),
                    "audio_url": p.get('audio', '')
                })

        first_meaning = dict_data[0]['meanings'][0]
        pos = first_meaning.get('partOfSpeech', 'N/A')
        def_info = first_meaning['definitions'][0]
        def_en = def_info.get('definition', '(No Definition)')
        def_vi = translate_word(session, def_en)  # Cần phiên bản async
        example = def_info.get('example', '(No Example)')
        fallback = f"Definition: {def_vi}\nExample: {example}"

        return pronunciations, pos, fallback
    except (KeyError, IndexError):
        return [], "N/A", "(Error parsing dictionary data)"

def translate_word(text_to_translate, source_lang = 'en', target_lang = 'vi'):
    """
        Dịch văn bản sử dụng MyMemory API.

        Args:
            text_to_translate (str): Đoạn văn bản cần dịch.
            source_lang (str): Mã ngôn ngữ nguồn (mặc định là 'en').
            target_lang (str): Mã ngôn ngữ đích (mặc định là 'vi').

        Returns:
            str: Đoạn văn bản đã được dịch, hoặc None nếu có lỗi.
    """
    if not isinstance(text_to_translate, str) or not text_to_translate:
        print(f"CẢNH BÁO: translate_word nhận được kiểu dữ liệu không hợp lệ: {type(text_to_translate)}")
        return None  # Hoặc trả về chuỗi rỗng ""

    encoded_text = urllib.parse.quote(text_to_translate)
    url = f'https://api.mymemory.translated.net/get?q={encoded_text}&langpair={source_lang}|{target_lang}'
    try:
        response = requests.get(url)

        # check connect status
        if response.status_code == 400:
            print(f"API request failed with status code {response.status_code}")
            return None
        # check response
        response.raise_for_status()
        data = response.json()

        if 'responseData' in data and 'translatedText' in data['responseData']:
            return data['responseData']['translatedText']
        else:
            print("API response does not contain 'responseData' or 'translatedText'")
            return None
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return None

def parse_gemini_response(text):
    if not text:
        return [], "N/A", None

    pronunciations = []
    pos = "N/A"
    explanation = text

    # Trích xuất phiên âm UK
    uk_match = re.search(r"^Phonetic UK:\s*(.*)", explanation, re.I | re.M)
    if uk_match:
        pronunciations.append({"region": "UK", "phonetic_text": uk_match.group(1).strip()})
        explanation = re.sub(r"^Phonetic UK:.*(\r\n?|\n)", "", explanation, count=1, flags=re.I | re.M).strip()

    # Trích xuất phiên âm US
    us_match = re.search(r"^Phonetic US:\s*(.*)", explanation, re.I | re.M)
    if us_match:
        pronunciations.append({"region": "US", "phonetic_text": us_match.group(1).strip()})
        explanation = re.sub(r"^Phonetic US:.*(\r\n?|\n)", "", explanation, count=1, flags=re.I | re.M).strip()

    pos_match = re.search(r"^Part of speech:\s*(.*)", explanation, re.I | re.M)
    if pos_match:
        pos = pos_match.group(1).strip()
        explanation = re.sub(r"^Part of speech:.*(\r\n?|\n)", "", explanation, count=1, flags=re.I | re.M).strip()

    return pronunciations, pos, explanation.strip()

def display_result(word, pronunciations, pos, explanation, fallback_info):
    print(f"Best definition for: '{word}'")
    print(f"Part of Speech: {pos}")
    print(f"Phonetic: ")
    if pronunciations:
        for p in pronunciations:
            print(f"  - {p.get('region', 'N/A')}: {p.get('phonetic_text', 'N/A')}")
    else:
        print("  - Không tìm thấy.")
    print("Explanation: ")
    if explanation:
        print(f"{explanation}")
    else:
        print(f"{fallback_info}")

def generate_audio_from_text(text, save_dir_name="audio"):
    try:
        # Giả định thư mục gốc là thư mục cha của 'src'
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        audio_folder = os.path.join(project_root, save_dir_name)
        os.makedirs(audio_folder, exist_ok=True)

        safe_filename = re.sub(r'[\\/*?:"<>|]', "", text).replace(" ", "_") + ".mp3"
        file_path = os.path.join(audio_folder, safe_filename)

        if os.path.exists(file_path):
            print(f"DEBUG: File âm thanh '{file_path}' đã tồn tại.")
            return file_path

        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(file_path)
        print(f"DEBUG: Đã tạo file âm thanh tại '{file_path}'")
        return file_path
    except Exception as e:
        print(f"Lỗi khi tạo file âm thanh cho '{text}': {e}")
        return None

def convert_gemini_response_to_db_format(word, gemini_response_text):
    """
    Hàm mới: Chỉ phân tích phản hồi thô từ Gemini và tạo word_data.
    """
    if not gemini_response_text:
        return None

    word_data = {
        'word_name': word,
        'pronunciations': [],
        'meanings': []
    }

    # Phân tích pronunciations
    uk_match = re.search(r"^Phonetic UK:\s*(.*)", gemini_response_text, re.I | re.M)
    us_match = re.search(r"^Phonetic US:\s*(.*)", gemini_response_text, re.I | re.M)
    if uk_match:
        word_data['pronunciations'].append({"region": "UK", "phonetic_text": uk_match.group(1).strip()})
    if us_match:
        word_data['pronunciations'].append({"region": "US", "phonetic_text": us_match.group(1).strip()})

    # Phân tích meanings
    pos_match = re.search(r"^Part of speech:\s*(.*)", gemini_response_text, re.I | re.M)
    def_en_match = re.search(r"Simple Definition English\s*:\s*(.*)", gemini_response_text, re.I)
    def_vi_match = re.search(r"Simple Definition Vietnamese\s*:\s*(.*)", gemini_response_text, re.I)
    example_match = re.search(r"-\s*\[?(.*?)\]?\s*\(\[?(.*?)\]?\)", gemini_response_text, re.I)

    meaning_info = {
        'part_of_speech': pos_match.group(1).strip() if pos_match else "N/A",
        'definition_en': def_en_match.group(1).strip() if def_en_match else "",
        'definition_vi': def_vi_match.group(1).strip() if def_vi_match else "",
        'example_en': example_match.group(1).strip() if example_match else "",
        'example_vi': example_match.group(2).strip() if example_match else ""
    }
    word_data['meanings'].append(meaning_info)

    return word_data


async def lookup_and_build_data(session, word):
    """
    Hàm này CHỈ tra cứu, phân tích và kết hợp dữ liệu từ các API.
    Nó KHÔNG tạo ra file TTS.
    """
    word = word.strip().lower()

    if word in api_cache:
        return api_cache[word]

    gemini_task = asyncio.create_task(prompt_gemini_async(word))
    dict_task = asyncio.create_task(get_dictionary_data_async(session, word))
    gemini_response_text, dict_data = await asyncio.gather(gemini_task, dict_task)

    # --- BƯỚC 1: LUÔN LẤY DỮ LIỆU CƠ BẢN TỪ GEMINI ---
    word_data = convert_gemini_response_to_db_format(word, gemini_response_text)
    if not word_data:
        word_data = {'word_name': word, 'pronunciations': [], 'meanings': []}

    # --- BƯỚC 2: TRÍCH XUẤT CÁC PHIÊN ÂM CÓ AUDIO TỪ TỪ ĐIỂN ---
    dict_pron_with_audio = []
    if dict_data and isinstance(dict_data, list) and dict_data[0].get('phonetics'):
        for p in dict_data[0]['phonetics']:
            if p.get('audio'):
                region = "US" if "us.mp3" in p['audio'] else "UK" if "uk.mp3" in p['audio'] else None
                if region:
                    dict_pron_with_audio.append({
                        "region": region,
                        "phonetic_text": p.get('text', ''),
                        "audio_url": p.get('audio')
                    })

    # --- BƯỚC 3: KẾT HỢP DỮ LIỆU MỘT CÁCH THÔNG MINH ---
    final_pronunciations = word_data.get('pronunciations', [])

    for dict_pron in dict_pron_with_audio:
        region_to_match = dict_pron['region']
        gemini_pron_match = next((p for p in final_pronunciations if p.get('region') == region_to_match), None)

        if gemini_pron_match:
            # Nâng cấp phiên âm từ Gemini với audio_url từ từ điển
            gemini_pron_match['audio_url'] = dict_pron['audio_url']
            if dict_pron['phonetic_text']:
                gemini_pron_match['phonetic_text'] = dict_pron['phonetic_text']
        else:
            # Thêm phiên âm mới từ từ điển nếu Gemini không có
            final_pronunciations.append(dict_pron)

    word_data['pronunciations'] = final_pronunciations

    # BƯỚC 4: XÓA BỎ LOGIC TẠO TTS KHỎI ĐÂY

    api_cache[word] = word_data
    return word_data

async def run_lookup(session, word, topic_id_to_save, user_id_to_save):
    """Hàm này bây giờ sẽ gọi hàm tra cứu và sau đó lưu."""
    # 1. Tra cứu và lấy dữ liệu
    word_data_for_db = await lookup_and_build_data(session, word)

    if not word_data_for_db:
        print(f"Không tìm thấy dữ liệu cho '{word}'.")
        return

    # 2. Lưu vào CSDL
    print(f"Bắt đầu lưu vào CSDL cho user_id={user_id_to_save}...")

    # --- BƯỚC 2: LUÔN LUÔN THỰC HIỆN XỬ LÝ VÀ LƯU VÀO CSDL ---
    cached_data = api_cache[word]
    dict_data_raw = cached_data['dict_data_raw']  # Lấy dữ liệu thô từ cache

    word_data_for_db = convert_gemini_response_to_db_format(word, cached_data, dict_data_raw)
    print(f"\nDEBUG: Dữ liệu đã chuẩn hóa để lưu vào CSDL cho user {user_id_to_save}:\n{word_data_for_db}\n")

    from src.services.query_data.query_data import QueryData
    print(f"Bắt đầu lưu vào CSDL cho user_id={user_id_to_save}...")
    query_data = QueryData()
    try:
        result = await asyncio.to_thread(
            query_data.add_word_to_topic,
            target_topic_id=topic_id_to_save,
            word_data=word_data_for_db,
            user_id=user_id_to_save
        )
        if result["success"]:
            print(f"Đã lưu '{word}' vào CSDL thành công cho user_id={user_id_to_save}!")
        else:
            print(f"Lưu '{word}' vào CSDL thất bại cho user_id={user_id_to_save}: {result['error']}")
    except Exception as e:
        print(f"Lỗi không mong muốn khi lưu CSDL: {e}")

    display_result(word, cached_data['pos'], cached_data['explanation'], cached_data['fallback_info'])

# async def main():
#     async with aiohttp.ClientSession() as session:
#         tasks = [
#             run_lookup(session, "hello", 1, 1),  # Ví dụ: topic_id=1, user_id=1
#             run_lookup(session, "take a rain check", 1, 1),
#             run_lookup(session, "hello", 2, 2),  # Ví dụ: topic_id=1, user_id=1
#             run_lookup(session, "take a rain check", 2, 2),
#             run_lookup(session, "food", 2, 2),  # Ví dụ: topic_id=1, user_id=1
#             run_lookup(session, "so far so good", 2, 2),
#             run_lookup(session, "hi", 2, 2),  # Ví dụ: topic_id=1, user_id=1
#             run_lookup(session, "rain", 2, 2),
#             run_lookup(session, "tomato", 2, 2),  # Ví dụ: topic_id=1, user_id=1
#             run_lookup(session, "potato", 2, 2),
#         ]
#         await asyncio.gather(*tasks)
#
# if __name__ == "__main__":
#     asyncio.run(main())
