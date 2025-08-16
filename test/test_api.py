import requests
import urllib.parse # thư viện xử lý url
import re
import google.generativeai as genai
import os

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

def call_dictionaryapi_dev(word):
    """
    Gọi API DictionaryAPI.dev và trả về dữ liệu JSON nếu thành công.
    Ném ra Exception nếu có lỗi mạng hoặc không tìm thấy từ (404).
    """
    url = f'https://api.dictionaryapi.dev/api/v2/entries/en/{word}'
    response = requests.get(url)

    if response.status_code != 200:
        return None
    # Dòng này sẽ tự động ném ra Exception nếu status code là 4xx hoặc 5xx
    response.raise_for_status()
    return response.json()

def call_wiktionary_api(word):
    """
    Gọi API của Wiktionary và chuyển đổi kết quả về định dạng giống
    như DictionaryAPI.dev để xử lý nhất quán.
    """
    url = f'https://en.wiktionary.org/api/rest_v1/page/definition/{word}'
    response = requests.get(url)

    if response.status_code != 200:
        return None
    response.raise_for_status()
    wiktionary_data = response.json()

    # --- Bắt đầu sơ chế (transform) ---
    if 'en' not in wiktionary_data or not wiktionary_data['en']:
        return None

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

def prompt_definition_from_gemini(word_to_define):
    """
    Gọi API của Gemini và chuyển đổi kết quả về định dạng giống
    như DictionaryAPI.dev để xử lý nhất quán.
    """

    prompt = f"""
    Chỉ cần giair thích từ không cần ghi thêm bất cứ từ gì hay câu gì không liên quan
    Giải thích từ "{word_to_define}" bằng tiếng Anh và tiếng việt một cách thật đơn giản cho người mới học một cách dễ hiểu, tính liên quan, ngữ cảnh thực tế và khả năng ghi nhớ và không dùng định nghĩa trong từ điển
    Thêm phần dịch nghĩa tiếng việt cho ví dụ
    Sau đó, cung cấp 3 câu ví dụ rất phổ biến và tự nhiên trong giao tiếp hàng ngày.

    Định dạng đầu ra phải như sau:
    Simple Definition English : [định nghĩa tiếng anh của bạn ở đây]
    Simple Definition Vietnamese : [định nghĩa tiếng việt của bạn ở đây]
    Common Examples :
    1. [câu ví dụ 1] ([câu việt dụ 1])
    2. [câu ví dụ 2] ([câu việt dụ 2])
    3. [câu ví dụ 3] ([câu việt dụ 3])
    """
    # --- Gửi yêu cầu đến Gemini và nhận kết quả ---
    try:
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Đã xảy ra lỗi khi gọi API: {e}")
        return "Sorry, an error occurred while generating the explanation."


def get_word_data_with_fallback(word):
    """
    Thử lấy dữ liệu từ DictionaryAPI.dev trước.
    Nếu thất bại, tự động chuyển sang dùng Wiktionary API.
    """
    try:
        # Ưu tiên gọi API #1 (DictionaryAPI.dev)
        print(">>> Trying DictionaryAPI.dev...")
        data = call_dictionaryapi_dev(word)
        print(">>> DictionaryAPI.dev successful!\n")
        if data:
            return data
    except Exception as e:
        print(f"--- DictionaryAPI.dev failed: {e}")

    # Nếu API #1 thất bại, tự động chuyển sang API #2 (Wiktionary)
    try:
        print(">>> Falling back to Wiktionary API...")
        data = call_wiktionary_api(word)
        print(">>> Wiktionary API successful!\n")
        return data
    except Exception as e:
        print(f"--- Wiktionary API also failed: {e}")
        return None

def get_best_definition(word_data):
    if not word_data:
        return None, None

    pos_priority = ['noun', 'verb', 'adjective', 'adverb', 'interjection']

    for entry in word_data:
        for pos in pos_priority:
            for meaning in entry.get('meanings', []):
                if meaning.get('partOfSpeech') == pos:
                    # for definition_info in meaning.get('definitions', []):
                    #     if 'example' in definition_info and definition_info['example']:
                            # definition = translate_word(definition_info.get('definition')) or definition_info.get('definition')
                    definition = prompt_definition_from_gemini(word_data)
                            # example = definition_info.get('example')
                    return definition, pos

    for entry in word_data:
        for meaning in entry.get('meanings', []):
            # for definition_info in meaning.get('definitions', []):
                # if 'example' in definition_info and definition_info['example']:
                    # definition = translate_word(definition_info.get('definition')) or definition_info.get('definition')
                definition = prompt_definition_from_gemini(word_data)
                    # example = definition_info.get('example')
                return definition, meaning.get('partOfSpeech')

    try:
        first_meaning = word_data[0]['meanings'][0]
        # first_definition = first_meaning['definitions'][0]['definition']
        return {
            # first_definition.get('definition'),
            prompt_definition_from_gemini(word_data),
            first_meaning.get('partOfSpeech')
        }
    except (KeyError, IndexError):
        return None, None

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

def test_api(word):
   try:
       # call API
       data = get_word_data_with_fallback(word)

       definition, pos = get_best_definition(data)

       # print result
       if definition:
           print(f"Best definition for '{word}':")
           print(f"Part of Speech: {pos}")
           print(f"{definition}")
       else:
           print(f"No definition found for '{word}'")

   except requests.exceptions.RequestException as e:
       print(f"API request failed: {e}")
       return

if __name__ == "__main__":
    test_api("food")