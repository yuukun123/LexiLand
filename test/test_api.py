import requests
import urllib.parse # thư viện xử lý url
import re

def call_dictionaryapi_dev(word):
    """
    Gọi API DictionaryAPI.dev và trả về dữ liệu JSON nếu thành công.
    Ném ra Exception nếu có lỗi mạng hoặc không tìm thấy từ (404).
    """
    url = f'https://api.dictionaryapi.dev/api/v2/entries/en/{word}'
    response = requests.get(url)
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



def get_word_data_with_fallback(word):
    """
    Thử lấy dữ liệu từ DictionaryAPI.dev trước.
    Nếu thất bại, tự động chuyển sang dùng Wiktionary API.
    """
    # try:
    #     # Ưu tiên gọi API #1 (DictionaryAPI.dev)
    #     print(">>> Trying DictionaryAPI.dev...")
    #     data = call_dictionaryapi_dev(word)
    #     print(">>> DictionaryAPI.dev successful!")
    #     if data:
    #         return data
    # except Exception as e:
    #     print(f"--- DictionaryAPI.dev failed: {e}")

    # Nếu API #1 thất bại, tự động chuyển sang API #2 (Wiktionary)
    try:
        print("\n>>> Falling back to Wiktionary API...")
        data = call_wiktionary_api(word)
        print(">>> Wiktionary API successful!")
        return data
    except Exception as e:
        print(f"--- Wiktionary API also failed: {e}")
        return None  # Cả hai đều thất bại

def test_api(word):
   try:
       # call API
       data = get_word_data_with_fallback(word)

       definition, example, pos = get_best_definition(data)

       # print result
       if definition:
           print(f"Best definition for '{word}':")
           print(f"Definition: {definition}")
           print(f"Example: {example}")
           print(f"Part of Speech: {pos}")
       else:
           print(f"No definition found for '{word}'")

   except requests.exceptions.RequestException as e:
       print(f"API request failed: {e}")
       return

def get_best_definition(word_data):
    if not word_data:
        return None, None, None

    pos_priority = ['noun', 'verb', 'adjective', 'adverb', 'interjection']

    for entry in word_data:
        for pos in pos_priority:
            for meaning in entry.get('meanings', []):
                if meaning.get('partOfSpeech') == pos:
                    for definition_info in meaning.get('definitions', []):
                        if 'example' in definition_info and definition_info['example']:
                            definition = translate_word(definition_info.get('definition')) or definition_info.get('definition')
                            example = definition_info.get('example')
                            return definition, example, pos

    for entry in word_data:
        for meaning in entry.get('meanings', []):
            for definition_info in meaning.get('definitions', []):
                if 'example' in definition_info and definition_info['example']:
                    definition = translate_word(definition_info.get('definition')) or definition_info.get('definition')
                    example = definition_info.get('example')
                    return definition, example, meaning.get('partOfSpeech')

    try:
        first_meaning = word_data[0]['meanings'][0]
        first_definition = first_meaning['definitions'][0]['definition']
        return {
            first_definition.get('definition'),
            first_definition.get('example', 'N/A'),
            first_meaning.get('partOfSpeech')
        }
    except (KeyError, IndexError):
        return None, None, None

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

if __name__ == "__main__":
    test_api("food")