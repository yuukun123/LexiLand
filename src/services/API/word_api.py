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

# async def prompt_gemini_async(word_to_define):
#     """
#     Gọi API của Gemini và chuyển đổi kết quả về định dạng giống
#     như DictionaryAPI.dev để xử lý nhất quán.
#     """
#     if check_multi_word_phrase(word_to_define):
#         prompt_header = f"""
#         Chỉ cần giải thích cụm từ hoặc thành ngữ và tối đa 11 từ không cần ghi thêm bất cứ từ gì hay câu gì không liên quan
#         Giải thích từ "{word_to_define}" bằng tiếng Anh và tiếng việt một cách thật đơn giản cho người mới học một cách dễ hiểu, tính liên quan, ngữ cảnh thực tế và khả năng ghi nhớ và không dùng định nghĩa trong từ điển
#         Thêm phiên âm Uk
#         Thêm phiên âm US
#         Thêm loại từ cho cụm từ hoặc thành ngữ không cần tiếng việt
#         Thêm phần dịch nghĩa tiếng việt cho ví dụ
#         Sau đó, cung cấp 1 câu ví dụ rất phổ biến và tự nhiên trong giao tiếp hàng ngày.
#         """
#
#     else:
#         prompt_header = f"""
#         cho tôi nghĩa tiếng việt của từ {word_to_define}, Thêm phiên âm UK và US.
#         cho tôi 2 câu ví dụ cả tiếng anh và tiếng việt của từ {word_to_define}
#         chỉ cho nghĩa không cần giải thích cụ thể nó là gì
#         """
#
#     prompt_footer = f"""
#         Định dạng đầu ra phải như sau:
#         Phonetic UK: [phiên âm UK]
#         Phonetic US: [phiên âm US]
#         Part of speech: [loại từ]
#         Simple Definition English : [định nghĩa tiếng anh của bạn ở đây]
#         Simple Definition Vietnamese : [định nghĩa tiếng việt của bạn ở đây]
#         Common Examples :
#         -[câu ví dụ] ([câu việt dụ])
#     """
#     full_prompt = prompt_header + prompt_footer
#     # --- Gửi yêu cầu đến Gemini và nhận kết quả ---
#     try:
#         # GIẢI PHÁP 3: GIỚI HẠN KẾT QUẢ ĐẦU RA
#         generation_config = genai.types.GenerationConfig(
#             max_output_tokens=512,
#             temperature=0.7
#         )
#         response = await gemini_model.generate_content_async(
#             full_prompt,
#             generation_config=generation_config
#         )
#         return response.text.strip()
#     except Exception as e:
#         print(f"Đã xảy ra lỗi khi gọi API cho '{word_to_define}': {e}")
#         return None
async def prompt_gemini_async(word_to_define):
    """
    Hàm tạo prompt đã được tối ưu hoàn toàn bằng tiếng Anh để tăng tốc độ.
    """
    # <<< TỐI ƯU 1: PROMPT TIẾNG ANH ĐỂ TĂNG TỐC ĐỘ >>>
    if check_multi_word_phrase(word_to_define):
        # Prompt cho Cụm từ / Thành ngữ
        prompt_header = f"""
            Analyze the idiom or phrase: "{word_to_define}".

            Your main goal is to explain it for a beginner learning English. The explanation must be simple, easy to understand, relevant, provide real-world context, and be memorable. **Do not use standard dictionary definitions.**

            Provide the following specific pieces of information:
            1. A very concise English explanation (maximum 11 words). Do not add any extra, unrelated sentences.
            2. A simple Vietnamese explanation.
            3. The UK and US phonetic transcriptions.
            4. The part of speech for the phrase (in English only).
            5. One very common and natural example sentence used in daily conversation, along with its Vietnamese translation.
            """
    else:
        # Prompt cho Từ đơn
        prompt_header = f"""
            Analyze the word: "{word_to_define}".

            Provide ONLY the following specific pieces of information. **Do not provide any detailed explanations of what the word is.**
            1. A simple Vietnamese meaning.
            2. The UK and US phonetic transcriptions.
            3. Two common example sentences, each provided in both English and Vietnamese.
            4. The part of speech.
            5. A simple English meaning.
            """

    prompt_format = """
        Your response MUST strictly follow this format, with no additional text or explanations:
        Phonetic UK: [UK phonetic transcription]
        Phonetic US: [US phonetic transcription]
        Part of speech: [part of speech]
        Simple Definition English: [English definition]
        Simple Definition Vietnamese: [Vietnamese definition]
        Common Examples:
        - [Example 1 in English] ([Example 1 in Vietnamese])
        - [Example 2 in English] ([Example 2 in Vietnamese])
    """
    full_prompt = prompt_header + prompt_format

    try:
        generation_config = genai.types.GenerationConfig(
            max_output_tokens=512,
            temperature=0.7
        )
        response = await gemini_model.generate_content_async(
            full_prompt,
            generation_config=generation_config
        )
        return response.text.strip()
    except Exception as e:
        print(f"Đã xảy ra lỗi khi gọi API cho '{word_to_define}': {e}")
        return None

async def check_spelling_with_gemini(word_to_check):
    prompt = f"""
    Analyze the English word "{word_to_check}". Check if it is spelled correctly.
    If it is misspelled, provide the correct spelling.
    Respond ONLY with a valid JSON object in this format, with no other text or markdown:
    {{"is_correct": boolean, "suggestion": "string"}}
    If the word is correct, "suggestion" should be an empty string.
    """
    try:
        response = await gemini_model.generate_content_async(prompt)
        clean_json_str = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json_str)
    except Exception as e:
        print(f"Lỗi khi kiểm tra chính tả: {e}")
        return {"is_correct": True, "suggestion": ""}

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
        'part_of_speech': pos_match.group(1).strip('[]()') if pos_match else "N/A",
        'definition_en': def_en_match.group(1).strip('[]()') if def_en_match else "",
        'definition_vi': def_vi_match.group(1).strip('[]()') if def_vi_match else "",
        'example_en': example_match.group(1).strip('[]()') if example_match else "",
        'example_vi': example_match.group(2).strip('[]()') if example_match else ""
    }
    word_data['meanings'].append(meaning_info)

    return word_data

async def get_word_data_from_gemini(word):
    """
    Hàm chính để tra cứu: chỉ gọi Gemini, phân tích và trả về dữ liệu có cấu trúc.
    """
    word = word.strip().lower()
    if word in api_cache:
        print(f"Lấy từ '{word}' từ cache.")
        return api_cache[word]

    print(f"Tra cứu từ '{word}' bằng API Gemini...")
    gemini_response_text = await prompt_gemini_async(word)

    if not gemini_response_text:
        print(f"Không nhận được phản hồi từ Gemini cho từ '{word}'.")
        return None

    word_data = convert_gemini_response_to_db_format(word, gemini_response_text)

    # Lưu vào cache để lần sau dùng lại
    api_cache[word] = word_data
    return word_data


# import asyncio
# import re
# import google.generativeai as genai
# import os
# import json
# from gtts import gTTS
#
# api_cache = {}
#
# # CÁCH CẤU HÌNH API KEY AN TOÀN VÀ ĐÚNG ĐẮN
# try:
#     GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
#     if not GOOGLE_API_KEY:
#         print("CẢNH BÁO: Không tìm thấy biến môi trường GOOGLE_API_KEY. Sử dụng key hardcode (CHỈ DÙNG ĐỂ TEST).")
#         GOOGLE_API_KEY = "AIzaSyBTlhhYZkFdzwmUBSsN98dpUC9X6pSO8Wg"  # Thay key của bạn vào đây
#
#     genai.configure(api_key=GOOGLE_API_KEY)
#
#     # GIẢI PHÁP 1: SỬ DỤNG MODEL NHANH NHẤT
#     gemini_model = genai.GenerativeModel('gemini-2.0-flash')
#     print(">>> Cấu hình Gemini API Key thành công với model gemini-1.5-flash-latest!")
#
# except Exception as e:
#     print(f"LỖI: Không thể cấu hình Gemini API Key: {e}.")
#     exit()
#
#
# def check_multi_word_phrase(text):
#     return ' ' in text.strip()
#
#
# async def prompt_gemini_async(word_to_define):
#     """
#     Hàm tạo prompt đã được tối ưu hoàn toàn bằng tiếng Anh để tăng tốc độ.
#     """
#     # GIẢI PHÁP 2: TỐI ƯU PROMPT BẰNG TIẾNG ANH
#     if check_multi_word_phrase(word_to_define):
#         prompt_content = f"""
#         Analyze the idiom or phrase: "{word_to_define}". Provide the following information concisely:
#         1. UK and US phonetic transcription.
#         2. Part of speech.
#         3. A simple English definition for a beginner.
#         4. A simple Vietnamese definition.
#         5. One common, natural example sentence with its Vietnamese translation.
#         """
#     else:
#         prompt_content = f"""
#         Analyze the word: "{word_to_define}". Provide the following information concisely:
#         1. UK and US phonetic transcription.
#         2. Part of speech.
#         3. A simple English definition for a beginner.
#         4. A simple Vietnamese definition.
#         5. Two common, natural example sentences with their Vietnamese translations.
#         """
#
#     prompt_format = """
#         Your response MUST strictly follow this format, with no additional text or explanations:
#         Phonetic UK: [UK phonetic transcription]
#         Phonetic US: [US phonetic transcription]
#         Part of speech: [part of speech]
#         Simple Definition English: [English definition]
#         Simple Definition Vietnamese: [Vietnamese definition]
#         Common Examples:
#         - [Example 1 in English] ([Example 1 in Vietnamese])
#         - [Example 2 in English] ([Example 2 in Vietnamese])
#     """
#     full_prompt = prompt_content + prompt_format
#
#     try:
#         # GIẢI PHÁP 3: GIỚI HẠN KẾT QUẢ ĐẦU RA
#         generation_config = genai.types.GenerationConfig(
#             max_output_tokens=512,
#             temperature=0.7
#         )
#         response = await gemini_model.generate_content_async(
#             full_prompt,
#             generation_config=generation_config
#         )
#         return response.text.strip()
#     except Exception as e:
#         print(f"Đã xảy ra lỗi khi gọi API cho '{word_to_define}': {e}")
#         return None
#
#
# def convert_gemini_response_to_db_format(word, gemini_response_text):
#     if not gemini_response_text: return None
#     word_data = {'word_name': word, 'pronunciations': [], 'meanings': []}
#
#     uk_match = re.search(r"Phonetic UK:\s*(.*)", gemini_response_text, re.I | re.M)
#     us_match = re.search(r"Phonetic US:\s*(.*)", gemini_response_text, re.I | re.M)
#     if uk_match: word_data['pronunciations'].append({"region": "UK", "phonetic_text": uk_match.group(1).strip()})
#     if us_match: word_data['pronunciations'].append({"region": "US", "phonetic_text": us_match.group(1).strip()})
#
#     pos_match = re.search(r"Part of speech:\s*(.*)", gemini_response_text, re.I | re.M)
#     def_en_match = re.search(r"Simple Definition English:\s*(.*)", gemini_response_text, re.I | re.M)
#     def_vi_match = re.search(r"Simple Definition Vietnamese:\s*(.*)", gemini_response_text, re.I | re.M)
#     examples = re.findall(r"-\s*(.*?)\s*\((.*?)\)", gemini_response_text, re.I | re.M)
#
#     meaning_info = {
#         'part_of_speech': pos_match.group(1).strip() if pos_match else "N/A",
#         'definition_en': def_en_match.group(1).strip() if def_en_match else "",
#         'definition_vi': def_vi_match.group(1).strip() if def_vi_match else "",
#         'examples': [{'en': en.strip(), 'vi': vi.strip()} for en, vi in examples]
#     }
#     word_data['meanings'].append(meaning_info)
#     return word_data
#
#
# async def get_word_data_from_gemini(word):
#     word = word.strip().lower()
#     if word in api_cache:
#         print(f"Lấy từ '{word}' từ cache.")
#         return api_cache[word]
#
#     gemini_response_text = await prompt_gemini_async(word)
#     if not gemini_response_text: return None
#
#     word_data = convert_gemini_response_to_db_format(word, gemini_response_text)
#     api_cache[word] = word_data
#     return word_data
#
#
# async def check_spelling_with_gemini(word_to_check):
#     prompt = f"""
#     Analyze the English word "{word_to_check}". Check if it is spelled correctly.
#     If it is misspelled, provide the correct spelling.
#     Respond ONLY with a valid JSON object in this format, with no other text or markdown:
#     {{"is_correct": boolean, "suggestion": "string"}}
#     If the word is correct, "suggestion" should be an empty string.
#     """
#     try:
#         response = await gemini_model.generate_content_async(prompt)
#         clean_json_str = response.text.strip().replace("```json", "").replace("```", "").strip()
#         return json.loads(clean_json_str)
#     except Exception as e:
#         print(f"Lỗi khi kiểm tra chính tả: {e}")
#         return {"is_correct": True, "suggestion": ""}