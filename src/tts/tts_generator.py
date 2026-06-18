# ==================================================
# 파일명: tts_generator.py
# 역할: 일본어 / 한국어 TTS 음성 생성 모듈
# ==================================================


# ==================================================
# 1. 라이브러리 import 섹션
# ==================================================

import edge_tts
import asyncio
import os
import json


# ==================================================
# 2. 기본 경로 설정 섹션
# ==================================================

audio_folder = "assets/audio"

if not os.path.exists(audio_folder):
    os.makedirs(audio_folder)


# ==================================================
# 3. 음성 모델 설정 섹션
# ==================================================

JAPANESE_VOICE = "ja-JP-NanamiNeural"
KOREAN_VOICE = "ko-KR-SunHiNeural"


# ==================================================
# 4. 공통 TTS 생성 함수 섹션
# ==================================================

async def create_tts(text, voice, save_path):
    if not text:
        print("텍스트가 비어 있어서 음성 생성을 건너뜁니다.")
        return

    try:
        communicator = edge_tts.Communicate(text, voice, rate="-15%")
        await communicator.save(str(save_path))

    except Exception as error:
        print(f"음성 생성 실패: {error}")


# ==================================================
# 5. 일본어 음성 생성 함수 섹션
# ==================================================

async def create_japanese_tts(text, filename):
    save_path = os.path.join(audio_folder, filename)
    await create_tts(text, JAPANESE_VOICE, save_path)


# ==================================================
# 6. 한국어 음성 생성 함수 섹션
# ==================================================

async def create_korean_tts(text, filename):
    save_path = os.path.join(audio_folder, filename)
    await create_tts(text, KOREAN_VOICE, save_path)


# ==================================================
# 7. 단어 데이터 불러오기 함수 섹션
# ==================================================

def load_words():
    try:
        with open("data/words.json", "r", encoding="utf-8") as files:
            words = json.load(files)
            return words

    except FileNotFoundError:
        print("data/words.json 파일을 찾을 수 없습니다.")
        return []

    except json.JSONDecodeError:
        print("words.json 파일 형식이 올바르지 않습니다.")
        return []


# ==================================================
# 8. 단어별 TTS 생성 처리 섹션
# ==================================================

async def generate_tts_from_words():
    words = load_words()

    if not words:
        print("처리할 단어 데이터가 없습니다.")
        return

    for item in words:
        word = item.get("word", "")
        hiragana = item.get("hiragana", "")
        meaning = item.get("meaning", "")
        romaji = item.get("romaji", "")

        if not romaji:
            print(f"{word} 의 romaji 값이 없어서 건너뜁니다.")
            continue

        jp_filename = f"{romaji}_jp.mp3"
        kr_filename = f"{romaji}_kr.mp3"

        print(f"처리 중: {word} / {hiragana} / {meaning}")

        await create_japanese_tts(
            hiragana,
            jp_filename
        )

        await create_korean_tts(
            meaning,
            kr_filename
        )

        print(f"생성 완료: {jp_filename}, {kr_filename}")


# ==================================================
# 9. 테스트 실행 섹션
# ==================================================

async def test():
    await generate_tts_from_words()


if __name__ == "__main__":
    asyncio.run(test())
