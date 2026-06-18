# ==================================================
# 파일명: video_batch_generator.py
# 역할: words.json의 모든 단어에 대해 쇼츠 mp4 영상을 자동 생성하는 모듈
# ==================================================


# ==================================================
# 1. 라이브러리 import 섹션
# ==================================================

import json

from src.video.video_generator import create_word_video


# ==================================================
# 2. 기본 경로 설정 섹션
# ==================================================

words_file = "data/words.json"


# ==================================================
# 3. 단어 데이터 불러오기 함수 섹션
# ==================================================

# - words.json 파일을 연다.
# - JSON 데이터를 읽는다.
# - 단어 목록을 반환한다.
# - 파일이 없거나 JSON 형식이 틀리면 빈 리스트를 반환한다.


    # 파일 읽기 중 오류가 나도 프로그램이 바로 멈추지 않게 한다.
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
# 4. 전체 영상 생성 함수 섹션
# ==================================================

# - 단어 목록을 불러온다.
# - 단어 목록이 비어 있으면 중단한다.
# - 단어 하나씩 반복한다.
# - romaji 값을 꺼낸다.
# - romaji가 없으면 건너뛴다.
# - create_word_video 함수를 실행한다.
# - 전체 완료 메시지를 출력한다.


def generate_all_videos():
    words = load_words()

    if not words:
        print("처리할 단어 데이터가 없습니다.")

        return


    for current_word in words:
        romaji = current_word.get("romaji", "")

        if not romaji:
            print("romaji 값이 없어서 영상 생성을 건너뜁니다.")

            continue

        create_word_video(romaji)

    print("전체 영상 생성 완료")


# ==================================================
# 5. 직접 실행 섹션
# ==================================================

# - 이 파일을 직접 실행했을 때 전체 영상 생성 함수를 실행한다.


if __name__ == "__main__":
    generate_all_videos()
