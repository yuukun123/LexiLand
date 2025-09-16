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

async def prompt_gemini_async(word_to_define):
    """
    Gọi API của Gemini và chuyển đổi kết quả về định dạng giống
    như DictionaryAPI.dev để xử lý nhất quán.
    """
    if check_multi_word_phrase(word_to_define):
        prompt_header = f"""
        Chỉ cần giải thích cụm từ hoặc thành ngữ không cần ghi thêm bất cứ từ gì hay câu gì không liên quan
        Giải thích từ "{word_to_define}" bằng tiếng Anh và tiếng việt một cách thật đơn giản cho người mới học một cách dễ hiểu, tính liên quan, ngữ cảnh thực tế và khả năng ghi nhớ và không dùng định nghĩa trong từ điển
        Thêm phiên âm Uk
        Thêm phiên âm US
        Thêm loại từ cho cụm từ hoặc thành ngữ không cần tiếng việt
        Thêm phần dịch nghĩa tiếng việt cho ví dụ
        Sau đó, cung cấp 1 câu ví dụ rất phổ biến và tự nhiên trong giao tiếp hàng ngày.
        """

    else:
        prompt_header = f"""
        Chỉ cần giải thích từ không cần ghi thêm bất cứ từ gì hay câu gì không liên quan
        Giải thích từ "{word_to_define}" bằng tiếng Anh và tiếng việt một cách thật đơn giản cho người mới học một cách dễ hiểu, tính liên quan, ngữ cảnh thực tế và khả năng ghi nhớ và không dùng định nghĩa trong từ điển
        Thêm phiên âm Uk
        Thêm phiên âm US
        Thêm phần dịch nghĩa tiếng việt cho ví dụ
        Sau đó, cung cấp 1 câu ví dụ rất phổ biến và tự nhiên trong giao tiếp hàng ngày.
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

async def parse_dictionary_data(session, dict_data):
    # if not dict_data or 'meanings' not in dict_data[0]:
    #     return "N/A", "N/A", "(Can't find this phrase in dictionary"
    # try:
    #     # Tìm định nghĩa đầu tiên CÓ CẢ VÍ DỤ
    #     phonetic = dict_data[0].get('phonetic', 'N/A')
    #     for meaning in dict_data[0].get('meanings', []):
    #         part_of_speech = meaning.get('partOfSpeech', 'N/A')
    #         for definition_info in meaning.get('definitions', []):
    #             if 'example' in definition_info and 'definition' in definition_info:
    #                 definition_EN = definition_info['definition']
    #                 definition_VN = translate_word(definition_info.get('definition', '(No Definition)'))
    #                 example = definition_info['example']
    #                 fallback_text = f"Definition: {definition_EN}\nDefinition Vietnamese: {definition_VN}\nExample: {example}"
    #                 return phonetic, part_of_speech, fallback_text
    #
    #     # Nếu không có cái nào có cả 2, lấy cái đầu tiên có thể
    #     phonetic = dict_data[0].get('phonetic', 'N/A')
    #     first_meaning = dict_data[0]['meanings'][0]
    #     part_of_speech = first_meaning.get('partOfSpeech', 'N/A')
    #     first_definition_info = first_meaning['definitions'][0]
    #     definition_EN = first_definition_info.get('definition', '(No Definition)')
    #     definition_VN = translate_word(first_definition_info.get('definition', '(No Definition)'))
    #     example = first_definition_info.get('example', '(No Example)')
    #     fallback_text = f"Definition English: {definition_EN}\nDefinition Vietnamese: {definition_VN}\nExample: {example}"
    #     return phonetic, part_of_speech, fallback_text
    # except (KeyError, IndexError):
    #     return "N/A", "N/A", "(Lỗi xử lý dữ liệu từ điển)"

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
        def_vi = await translate_text_async(session, def_en)  # Cần phiên bản async
        example = def_info.get('example', '(No Example)')
        fallback = f"Definition: {def_vi}\nExample: {example}"

        return pronunciations, pos, fallback
    except (KeyError, IndexError):
        return [], "N/A", "(Error parsing dictionary data)"

# def translate_word(text_to_translate, source_lang = 'en', target_lang = 'vi'):
#     """
#         Dịch văn bản sử dụng MyMemory API.
#
#         Args:
#             text_to_translate (str): Đoạn văn bản cần dịch.
#             source_lang (str): Mã ngôn ngữ nguồn (mặc định là 'en').
#             target_lang (str): Mã ngôn ngữ đích (mặc định là 'vi').
#
#         Returns:
#             str: Đoạn văn bản đã được dịch, hoặc None nếu có lỗi.
#     """
#     if not text_to_translate:
#         return None
#
#     encoded_text = urllib.parse.quote(text_to_translate)
#     url = f'https://api.mymemory.translated.net/get?q={encoded_text}&langpair={source_lang}|{target_lang}'
#     try:
#         response = requests.get(url)
#
#         # check connect status
#         if response.status_code == 400:
#             print(f"API request failed with status code {response.status_code}")
#             return None
#         # check response
#         response.raise_for_status()
#         data = response.json()
#
#         if 'responseData' in data and 'translatedText' in data['responseData']:
#             return data['responseData']['translatedText']
#         else:
#             print("API response does not contain 'responseData' or 'translatedText'")
#             return None
#     except requests.exceptions.RequestException as e:
#         print(f"API request failed: {e}")
#         return None

async def translate_text_async(session, text):
    if not isinstance(text, str) or not text: return text
    encoded_text = urllib.parse.quote(text)
    url = f"https://api.mymemory.translated.net/get?q={encoded_text}&langpair=en|vi"
    try:
        async with session.get(url, timeout=5) as response:
            if response.status == 200:
                data = await response.json()
                return data.get('responseData', {}).get('translatedText', text)
    except Exception: pass
    return text

def parse_gemini_response(text):
    # if not text: return "N/A", "N/A", None
    #
    # phonetic = "N/A"
    # pos = "N/A"
    # explanation = text
    #
    # phonetic_match = re.search(r"^Phonetic:\s*(.*)", explanation, re.IGNORECASE | re.MULTILINE)
    # if phonetic_match:
    #     phonetic = phonetic_match.group(1).strip()
    #     # Xóa dòng đã trích xuất
    #     explanation = re.sub(r"^Phonetic:.*(\r\n?|\n)", "", explanation, count=1, flags=re.IGNORECASE | re.MULTILINE).strip()
    #
    # pos_match = re.search(r"^Part of speech:\s*(.*)", explanation, re.IGNORECASE | re.MULTILINE)
    # if pos_match:
    #     pos = pos_match.group(1).strip()
    #     # Xóa dòng đã trích xuất
    #     explanation = re.sub(r"^Part of speech:.*(\r\n?|\n)", "", explanation, count=1, flags=re.IGNORECASE | re.MULTILINE).strip()
    #
    # return phonetic, pos, explanation

    """Trích xuất thông tin từ Gemini. Luôn trả về một danh sách pronunciations."""
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

# async def run_lookup(word):
#     if word in api_cache:
#         print(f"Best definition for '{word}':")
#         cached_data = api_cache[word]
#         display_result(word, cached_data['phonetic'], cached_data['pos'], cached_data['explanation'], cached_data['fallback_info'])
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
#     gemini_phonetic, gemini_pos, gemini_explanation = parse_gemini_response(gemini_response_text)
#     dict_phonetic, dict_pos, dict_fallback = await extract_pos_from_data(session, dict_data)
#     final_pos = dict_pos if dict_pos != "N/A" else gemini_pos
#     final_phonetic = dict_phonetic if dict_phonetic != "N/A" else gemini_phonetic
#
#     api_cache[word] = {
#         "phonetic": final_phonetic,
#         "pos": final_pos,
#         "explanation": gemini_explanation,
#         "fallback_info": dict_fallback,
#         "dict_data_raw": dict_data
#     }
#
#     display_result(word, final_phonetic, final_pos, gemini_explanation, dict_fallback)
#
# async def main():
#     await run_lookup("run")
#
# if __name__ == "__main__":
#     asyncio.run(main())

async def run_lookup(session, word):
    if word in api_cache:
        cached_data = api_cache[word]
        display_result(word, cached_data['pronunciations'], cached_data['pos'], cached_data['explanation'], cached_data['fallback_info'])
        return

    gemini_task = asyncio.create_task(prompt_gemini_async(word))
    dict_task = asyncio.create_task(get_dictionary_data_async(session, word))
    gemini_response_text, dict_data = await asyncio.gather(gemini_task, dict_task)

    # Tất cả các hàm parser bây giờ trả về cùng một cấu trúc (list, str, str)
    gemini_pron, gemini_pos, gemini_explanation = parse_gemini_response(gemini_response_text)
    dict_pron, dict_pos, dict_fallback = await parse_dictionary_data(session, dict_data)

    # Logic kết hợp đúng: Nếu danh sách từ điển không rỗng, dùng nó.
    final_pron = dict_pron if dict_pron else gemini_pron
    final_pos = dict_pos if dict_pos != "N/A" else gemini_pos

    # Lưu vào cache với cấu trúc nhất quán
    api_cache[word] = {
        "pronunciations": final_pron,  # <-- Key là 'pronunciations'
        "pos": final_pos,
        "explanation": gemini_explanation,
        "fallback_info": dict_fallback,
        "dict_data_raw": dict_data
    }

    # Gọi hàm display với các tham số đúng
    display_result(word, final_pron, final_pos, gemini_explanation, dict_fallback)


async def main():
    words_to_lookup = ["run", "love", "take a rain check"]
    async with aiohttp.ClientSession() as session:
        tasks = [run_lookup(session, word) for word in words_to_lookup]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
    print("program stop")
