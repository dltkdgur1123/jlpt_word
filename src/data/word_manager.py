# ==================================================
# 파일명: word_manager.py
# 역할: JLPT 단어 데이터를 words.json에 추가/저장/관리하는 모듈
# ==================================================


# ==================================================
# 1. 라이브러리 import 섹션
# ==================================================

import os
import json


# ==================================================
# 2. 기본 경로 설정 섹션
# ==================================================

BASE_DIR = os.path.abspath(os.getcwd())

data_folder = os.path.join(BASE_DIR, "data")

words_file = os.path.join(data_folder, "words.json")

if not os.path.exists(data_folder):
    os.makedirs(data_folder)


# ==================================================
# 3. 단어 목록 불러오기 함수 섹션
# ==================================================

# - words.json 파일을 연다.
# - JSON 데이터를 읽는다.
# - 단어 목록을 반환한다.
# - 파일이 없으면 빈 리스트를 반환한다.
# - JSON 형식이 잘못되면 빈 리스트를 반환한다.


def load_words():
    if not os.path.exists(words_file):
        return []


    try:
        with open(words_file, "r", encoding="utf-8") as file:
            words = json.load(file)
        
        return words
    
    except json.JSONDecodeError:
        print("words.json 형식이 올바르지 않습니다.")
        
        return []


# ==================================================
# 4. 단어 목록 저장 함수 섹션
# ==================================================

# - 단어 목록을 받는다.
# - words.json 파일을 쓰기 모드로 연다.
# - JSON 형식으로 저장한다.
# - 한글/일본어가 깨지지 않게 저장한다.


def save_words(words):
    with open(words_file, "w", encoding="utf-8") as file:
        json.dump(words, file, ensure_ascii=False, indent=4)


# ==================================================
# 5. 중복 단어 확인 함수 섹션
# ==================================================

# - 기존 단어 목록을 받는다.
# - 새 단어의 romaji를 받는다.
# - 같은 romaji가 이미 있으면 True를 반환한다.
# - 없으면 False를 반환한다.


def is_duplicate_word(words, romaji):
    for current_word in words:
        existing_romaji = current_word.get("romaji", "")

        if existing_romaji == romaji:
            return True

    return False


# ==================================================
# 6. 새 단어 만들기 함수 섹션
# ==================================================

# - word, hiragana, meaning, romaji 값을 받는다.
# - background_path를 자동으로 만든다.
# - 단어 딕셔너리를 만든다.
# - 단어 딕셔너리를 반환한다.


def create_word_item(word, hiragana, meaning, romaji, item_type="vocab", level="N1"):
    background_path = ("assets/backgrounds/default.jpg")
    
    new_word = {
        "type": item_type,
        "word": word,
        "hiragana": hiragana,
        "meaning": meaning,
        "romaji": romaji,
        "background_path": background_path,
        "level": level
    }

    return new_word


# ==================================================
# 7. 단어 추가 함수 섹션
# ==================================================

# - 기존 단어 목록을 불러온다.
# - 새 단어 데이터를 만든다.
# - romaji 중복 여부를 확인한다.
# - 중복이 아니면 단어 목록에 추가한다.
# - words.json에 저장한다.


def add_word(word, hiragana, meaning, romaji, item_type="vocab", level="N1"):
    words = load_words()


    if is_duplicate_word(words, romaji):

        print("이미 존재하는 단어입니다:", romaji)

        return False


    new_word = create_word_item(word, hiragana, meaning, romaji, item_type, level)

    words.append(new_word)

    save_words(words)

    print("단어 추가 완료:", word)

    return True

# ==================================================
# 8. 단어 목록 초기화 함수 섹션
# ==================================================

def clear_words():
    save_words([])
    print("words.json 초기화 완료")