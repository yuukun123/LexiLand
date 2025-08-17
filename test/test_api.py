import asyncio
import requests
import urllib.parse # thư viện xử lý url
import re
import google.generativeai as genai
import os
import aiohttp

from requests import session

api_cache = {}

# CÁCH ĐÚNG ĐỂ LẤY VÀ CẤU HÌNH API KEY
try:
    # Cách tốt nhất: Lấy key từ biến môi trường
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    if not GOOGLE_API_KEY:
        # Nếu không có biến môi trường, dùng key bạn hardcode (chỉ để test)
        print("Khoông tìm thấy biến môi trường. Dùng key hardcode.")
        # GOOGLE_API_KEY = "AIzaSyCwRytRMxm222OaWu4NXO7J6bEnN9S8_Zs" # <--- THAY BẰNG KEY THẬT CỦA BẠN
    genai.configure(api_key=GOOGLE_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-2.0-flash')
    print(">>> Cáu hình Gemini API Key thanh cong!")
except Exception as e:
    print(f"Lỗi cấu hình Gemini API Key: {e}. Hãy chắc chắn bạn đã đặt biến môi trường hoặc điền key vào code.")
    exit()

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
            if response.status_code == 200:
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
        response = await gemini_model.generate_content_async(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Đã xảy ra lỗi khi gọi API: {e}")
        return None

def extract_pos_from_data(dict_data):
    if not dict_data or 'meanings' not in dict_data[0]:
        return "N/A"
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

def display_result(word, pos, explanation, fallback_info):
    print(f"Best definition for '{word}':")
    print(f"Part of Speech: {pos}")
    if explanation:
        print(f"{explanation}")
    else:
        print(f"{fallback_info}")

async def run_lookup(word):
    if word in api_cache:
        print(f"Best definition for '{word}':")
        cached_data = api_cache[word]
        display_result(word, cached_data['pos'], cached_data['explanation'], cached_data['fallback_info'])
        return

    async with aiohttp.ClientSession() as session:
        dict_task = asyncio.create_task(get_dictionary_data_async(session, word))
        gemini_task = asyncio.create_task(prompt_definition_from_gemini(word))

        dict_data, gemini_explanation = await asyncio.gather(dict_task, gemini_task)

    part_of_speech, fallback_info = extract_pos_from_data(dict_data)

    api_cache[word] = {
        "pos": part_of_speech,
        "explanation": gemini_explanation,
        "fallback_info": fallback_info
    }

    display_result(word, part_of_speech, gemini_explanation, fallback_info)

async def main():
    await run_lookup("food")

if __name__ == "__main__":
    asyncio.run(main())
