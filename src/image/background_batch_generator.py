# ==================================================
# 파일명: background_batch_generator.py
# 역할: words.json의 모든 단어에 대해 AI 배경 이미지를 자동 생성하는 모듈
# ==================================================


# ==================================================
# 1. 라이브러리 import 섹션
# ==================================================


import os
import json

from src.image.prompt_generator import generate_image_prompt
from src.image.background_generator import generate_background_image
from src.utils.filename_utils import normalize_romaji_filename


# ==================================================
# 2. 기본 경로 설정 섹션
# ==================================================


# 단어 데이터가 들어있는 JSON 파일 위치
words_file = "data/words.json"

# - 생성된 AI 배경 이미지를 저장할 폴더
background_folder = "assets/backgrounds"


# ==================================================
# 3. 단어 데이터 불러오기 함수 섹션
# ==================================================

# - words.json 파일을 연다.
# - JSON 데이터를 읽는다.
# - 단어 목록을 반환한다.
# - 파일이 없거나 JSON 형식이 잘못되면 빈 리스트를 반환한다.


def load_words():

    try:
        with open(words_file, "r", encoding="utf-8") as file:
            words = json.load(file)

            return words


    except FileNotFoundError:
        print("words.json 파일을 찾을 수 없습니다.")

        return []


    except json.JSONDecodeError:
        print("words.json 형식이 올바르지 않습니다.")

        return []


# ==================================================
# 4. 단어별 배경 이미지 생성 함수 섹션
# ==================================================

# - 단어 데이터 1개를 받는다.
# - romaji 값을 꺼낸다.
# - romaji가 없으면 건너뛴다.
# - 저장 경로를 만든다.
# - 이미 같은 배경 이미지가 있으면 건너뛴다.
# - 이미지 프롬프트를 생성한다.
# - 배경 이미지를 생성한다.
# - 저장 경로를 반환한다.


def create_background_for_word(current_word):
    romaji = current_word.get("romaji", "")

    if not romaji:
        print("romaji 값이 없어서 배경 이미지 생성을 건너뜁니다.")

        return ""

    filename = normalize_romaji_filename(romaji) + ".png"

    save_path = os.path.join(background_folder, filename)

    if os.path.exists(save_path):
        print("이미 배경 이미지가 존재합니다:", save_path)

        return save_path

    image_prompt = generate_image_prompt(current_word)

    if not image_prompt:
        print("이미지 프롬프트 생성에 실패했습니다.")

        return ""

    generated_path = generate_background_image(
        image_prompt,
        save_path
    )

    return generated_path

# ==================================================
# 5. 전체 배경 이미지 생성 함수 섹션
# ==================================================

# - 단어 목록을 불러온다.
# - 단어 목록이 비어 있으면 중단한다.
# - 단어 하나씩 꺼낸다.
# - 각 단어마다 배경 이미지 생성 함수를 실행한다.
# - 전체 작업 완료 메시지를 출력한다.


def generate_all_backgrounds():
    words = load_words()

    if not words:
        print("처리할 단어 데이터가 없습니다.")
        return

    for current_word in words:
        create_background_for_word(current_word)

    print("전체 배경 이미지 생성 완료")

# ==================================================
# 6. 직접 실행 섹션
# ==================================================

# - 이 파일을 직접 실행했을 때 전체 배경 이미지 생성 함수를 실행한다.

if __name__ == "__main__":
    generate_all_backgrounds()
