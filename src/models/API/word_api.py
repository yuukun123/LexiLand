import asyncio
import requests
import urllib.parse # thư viện xử lý url
import re
import google.generativeai as genai
import os
import aiohttp
from gtts import gTTS
from requests import session

from src.models.query_data.query_data import QueryData

api_cache = {}

# CÁCH ĐÚNG ĐỂ LẤY VÀ CẤU HÌNH API KEY
try:
    # Cách tốt nhất: Lấy key từ biến môi trường
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    if not GOOGLE_API_KEY:
        # Nếu không có biến môi trường, dùng key bạn hardcode (chỉ để test)
        print("Khoông tìm thấy biến môi trường. Dùng key hardcode.")
        GOOGLE_API_KEY = "AIzaSyCwRytRMxm222OaWu4NXO7J6bEnN9S8_Zs" # <--- THAY BẰNG KEY THẬT CỦA BẠN
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

async def prompt_definition_from_gemini(word_to_define):
    """
    Gọi API của Gemini và chuyển đổi kết quả về định dạng giống
    như DictionaryAPI.dev để xử lý nhất quán.
    """
    if check_multi_word_phrase(word_to_define):
        prompt_header = f"""
        Chỉ cần giải thích cụm từ hoặc thành ngữ không cần ghi thêm bất cứ từ gì hay câu gì không liên quan
        Giải thích từ "{word_to_define}" bằng tiếng Anh và tiếng việt một cách thật đơn giản cho người mới học một cách dễ hiểu, tính liên quan, ngữ cảnh thực tế và khả năng ghi nhớ và không dùng định nghĩa trong từ điển
        Thêm Phiên âm cho cụm từ hoặc thành ngữu
        Thêm loại từ cho cụm từ hoặc thành ngữ không cần tiếng việt
        Thêm phần dịch nghĩa tiếng việt cho ví dụ
        Sau đó, cung cấp 1 câu ví dụ rất phổ biến và tự nhiên trong giao tiếp hàng ngày.
        """

    else:
        prompt_header = f"""
        Chỉ cần giải thích từ không cần ghi thêm bất cứ từ gì hay câu gì không liên quan
        Giải thích từ "{word_to_define}" bằng tiếng Anh và tiếng việt một cách thật đơn giản cho người mới học một cách dễ hiểu, tính liên quan, ngữ cảnh thực tế và khả năng ghi nhớ và không dùng định nghĩa trong từ điển
        thêm phien âm
        Thêm phần dịch nghĩa tiếng việt cho ví dụ
        Sau đó, cung cấp 1 câu ví dụ rất phổ biến và tự nhiên trong giao tiếp hàng ngày.
        """

    prompt_footer = f"""
        Định dạng đầu ra phải như sau:
        Phonetic: [phiên âm]
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

async def extract_pos_from_data(session, dict_data):
    if not dict_data or 'meanings' not in dict_data[0]:
        return "N/A", "(Can't find this phrase in dictionary"
    try:
        # Tìm định nghĩa đầu tiên CÓ CẢ VÍ DỤ
        for meaning in dict_data[0].get('meanings', []):
            part_of_speech = meaning.get('partOfSpeech', 'N/A')
            for definition_info in meaning.get('definitions', []):
                if 'example' in definition_info and 'definition' in definition_info:
                    definition_EN = definition_info['definition']
                    definition_VN = translate_word(definition_info.get('definition', '(No Definition)'))
                    example = definition_info['example']
                    fallback_text = f"Definition: {definition_EN}\nDefinition Vietnamese: {definition_VN}\nExample: {example}"
                    return part_of_speech, fallback_text

        # Nếu không có cái nào có cả 2, lấy cái đầu tiên có thể
        first_meaning = dict_data[0]['meanings'][0]
        part_of_speech = first_meaning.get('partOfSpeech', 'N/A')
        first_definition_info = first_meaning['definitions'][0]
        definition_EN = first_definition_info.get('definition', '(No Definition)')
        definition_VN = translate_word(first_definition_info.get('definition', '(No Definition)'))
        example = first_definition_info.get('example', '(No Example)')
        fallback_text = f"Definition English: {definition_EN}\nDefinition Vietnamese: {definition_VN}\nExample: {example}"
        return part_of_speech, fallback_text
    except (KeyError, IndexError):
        return "N/A", "(Lỗi xử lý dữ liệu từ điển)"

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
    if not text_to_translate:
        return None

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
    if not text: return "N/A", None
    match = re.search(r"^Part of speech:\s*(.*)", text, re.IGNORECASE | re.MULTILINE)
    if match:
        pos = match.group(1).strip()
        explanation = re.sub(r"^Part of speech:.*(\r\n?|\n)", "", text, count=1, flags=re.IGNORECASE | re.MULTILINE).strip()
        return pos, explanation
    return "N/A", text

def display_result(word, pos, explanation, fallback_info):
    print(f"Best definition for '{word}':")
    print(f"Part of Speech: {pos}")
    if explanation:
        print(f"{explanation}")
    else:
        print(f"{fallback_info}")

# async def run_lookup(word):
#     if word in api_cache:
#         print(f"Best definition for '{word}':")
#         cached_data = api_cache[word]
#         display_result(word, cached_data['pos'], cached_data['explanation'], cached_data['fallback_info'])
#         return
#
#     async with aiohttp.ClientSession() as session:
#         gemini_task = asyncio.create_task(prompt_definition_from_gemini(word))
#
#         dict_data = None
#         if not check_multi_word_phrase(word):
#             print("input is a single word")
#             dict_task = asyncio.create_task(get_dictionary_data_async(session, word))
#             dict_data, gemini_response_text = await asyncio.gather(dict_task, gemini_task)
#         else:
#             print("input is multi word")
#             gemini_response_text = await gemini_task
#
#
#     gemini_pos, gemini_explanation = parse_gemini_response(gemini_response_text)
#     dict_pos, dict_fallback = await extract_pos_from_data(session, dict_data)
#     final_pos = dict_pos if dict_pos != "N/A" else gemini_pos
#
#     api_cache[word] = {
#         "pos": final_pos,
#         "explanation": gemini_explanation,
#         "fallback_info": dict_fallback
#     }
#     query_data = QueryData()
#     query_data.add_word_to_topic(9, api_cache[word], 2)
#
#
#     display_result(word, final_pos, gemini_explanation, dict_fallback)
#
# async def main():
#     await run_lookup("food")

def generate_audio_from_text(text, save_dir="audio"):
    """
    Sử dụng gTTS để tạo file MP3 từ văn bản và lưu lại.
    Trả về đường dẫn đến file đã lưu.
    """
    try:
        # Tạo thư mục audio nếu chưa có
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        audio_folder = os.path.join(project_root, save_dir)
        os.makedirs(audio_folder, exist_ok=True)

        # Tạo tên file an toàn từ text
        safe_filename = re.sub(r'[\\/*?:"<>|]', "", text).replace(" ", "_") + ".mp3"
        file_path = os.path.join(audio_folder, safe_filename)

        # Nếu file đã tồn tại, không cần tạo lại
        if os.path.exists(file_path):
            print(f"DEBUG: File âm thanh '{file_path}' đã tồn tại.")
            return file_path

        # Tạo đối tượng gTTS
        tts = gTTS(text=text, lang='en', slow=False)
        # Lưu file
        tts.save(file_path)
        print(f"DEBUG: Đã tạo file âm thanh tại '{file_path}'")
        return file_path
    except Exception as e:
        print(f"Lỗi khi tạo file âm thanh cho '{text}': {e}")
        return None

def convert_cache_to_db_format(word, cached_data, dict_data):
    """
    Chuyển đổi dữ liệu từ cache và dữ liệu từ điển
    thành định dạng dictionary chuẩn để lưu vào CSDL (với bảng pronunciations).
    """
    word_data = {
        'word_name': word,
        'pronunciations': [],
        'meanings': []
    }

    # 1. Trích xuất thông tin từ Gemini (ưu tiên)
    explanation = cached_data.get('explanation')
    if explanation:
        phonetic_match = re.search(r"Phonetic:\s*(.*)", explanation, re.I)
        def_en_match = re.search(r"Simple Definition English\s*:\s*(.*)", explanation, re.I)
        def_vi_match = re.search(r"Simple Definition Vietnamese\s*:\s*(.*)", explanation, re.I)
        example_match = re.search(r"-\s*\[?(.*?)\]?\s*\(\[?(.*?)\]?\)", explanation, re.I)

        phonetic_text_from_gemini = phonetic_match.group(1).strip() if phonetic_match else ""

        meaning_info = {
            'part_of_speech': cached_data.get('pos', 'N/A'),
            'definition_en': def_en_match.group(1).strip() if def_en_match else "",
            'definition_vi': def_vi_match.group(1).strip() if def_vi_match else "",
            'example_en': example_match.group(1).strip() if example_match else "",
            'example_vi': example_match.group(2).strip() if example_match else ""
        }
        word_data['meanings'].append(meaning_info)

    # 2. Xử lý phần phát âm (pronunciations)
    pronunciations_list = []
    # Lấy URL âm thanh từ dữ liệu từ điển
    if dict_data and 'phonetics' in dict_data[0]:
        for phonetic_item in dict_data[0].get('phonetics', []):
            if 'audio' in phonetic_item and phonetic_item['audio']:
                pronunciations_list.append({
                    "phonetic_text": phonetic_item.get('text', ''),
                    "audio_url": phonetic_item['audio'],
                    # Cố gắng đoán vùng miền từ URL (ví dụ: 'us', 'uk')
                    "region": "US" if "us.mp3" in phonetic_item['audio'] else "UK" if "uk.mp3" in phonetic_item['audio'] else "Dict"
                })

    # Nếu không có audio từ từ điển, hãy TẠO RA nó bằng gTTS
    if not pronunciations_list:
        audio_path = generate_audio_from_text(word)  # Gọi hàm TTS
        phonetic_text = ""
        if cached_data.get('explanation'):
            phonetic_match = re.search(r"Phonetic:\s*(.*)", cached_data['explanation'], re.I)
            phonetic_text = phonetic_match.group(1).strip() if phonetic_match else ""

        pronunciations_list.append({
            "phonetic_text": phonetic_text,
            "audio_url": audio_path,  # Đây là đường dẫn file cục bộ
            "region": "TTS"
        })

    word_data['pronunciations'] = pronunciations_list
    return word_data


# ==========================================================
# SỬA LẠI HÀM run_lookup
# ==========================================================
async def run_lookup(session, word, topic_id_to_save, user_id_to_save):
    word = word.strip().lower()
    if word in api_cache:
        # Xử lý cache (nếu muốn, có thể gọi lại API để đảm bảo dữ liệu mới nhất)
        return

    print(f"\n--- Bắt đầu tra cứu cho '{word}' ---")

    gemini_task = asyncio.create_task(prompt_definition_from_gemini(word))
    dict_task = asyncio.create_task(get_dictionary_data_async(session, word))

    gemini_response_text, dict_data = await asyncio.gather(gemini_task, dict_task)

    gemini_pos, gemini_explanation = parse_gemini_response(gemini_response_text)
    dict_pos, dict_fallback = await extract_pos_from_data(session, dict_data)
    final_pos = dict_pos if dict_pos != "N/A" else gemini_pos

    api_cache[word] = {
        "pos": final_pos,
        "explanation": gemini_explanation,
        "fallback_info": dict_fallback,
        "dict_data_raw": dict_data  # Lưu dữ liệu thô từ từ điển để dùng sau
    }

    # --- THAY ĐỔI CHÍNH ---
    # Truyền cả dict_data vào hàm chuyển đổi
    word_data_for_db = convert_cache_to_db_format(word, api_cache[word], dict_data)
    print(f"\nDEBUG: Dữ liệu đã chuẩn hóa để lưu vào CSDL:\n{word_data_for_db}\n")

    print("Bắt đầu lưu vào CSDL...")
    query_data = QueryData()
    try:
        # Chạy hàm CSDL trong thread riêng
        result = await asyncio.to_thread(
            query_data.add_word_to_topic,
            target_topic_id=topic_id_to_save,
            word_data=word_data_for_db,
            user_id=user_id_to_save
        )
        if result["success"]:
            print(f"Đã lưu '{word}' vào CSDL thành công!")
        else:
            print(f"Lưu '{word}' vào CSDL thất bại: {result['error']}")
    except Exception as e:
        print(f"Lỗi không mong muốn khi lưu CSDL: {e}")

    display_result(word, final_pos, gemini_explanation, dict_fallback)


# --- Sửa lại hàm main để có thể chạy được ---
async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [
            run_lookup(session, "hello", 1, 1),  # Ví dụ: topic_id=1, user_id=1
            run_lookup(session, "take a rain check", 1, 1)
        ]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
