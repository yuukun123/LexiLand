import requests
import urllib.parse # thư viện xử lý url

def test_api(word):
   try:
       url = f'https://api.dictionaryapi.dev/api/v2/entries/en/{word}'
       response = requests.get(url)

       # check connect status
       if response.status_code == 400:
           print(f"API request failed with status code {response.status_code}")
           return
       # check response
       response.raise_for_status()
       data = response.json()

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
        return

    encoded_text = urllib.parse.quote(text_to_translate)

    url = f'https://api.mymemory.translated.net/get?q={encoded_text}&langpair={source_lang}|{target_lang}'

    try:
        response = requests.get(url)

        # check connect status
        if response.status_code == 400:
            print(f"API request failed with status code {response.status_code}")
            return
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
    test_api("hi")