# ==================================================
# 파일명: tts_generator.py
# 역할: 일본어 / 한국어 TTS 음성 생성 모듈
# ==================================================


# ==================================================
# 1. 라이브러리 import 섹션
# ==================================================

import asyncio
import json
import os
import re

import edge_tts
from src.utils.filename_utils import normalize_romaji_filename


# ==================================================
# 2. 기본 경로 설정 섹션
# ==================================================

AUDIO_FOLDER = "assets/audio"

os.makedirs(AUDIO_FOLDER, exist_ok=True)


# ==================================================
# 3. 음성 모델 설정 섹션
# ==================================================

JAPANESE_VOICE = "ja-JP-NanamiNeural"
KOREAN_VOICE = "ko-KR-SunHiNeural"

MAX_RETRIES = 3
MIN_AUDIO_SIZE = 512
QUESTION_MARK_ONLY_PATTERN = re.compile(r"^[?？\s]+$")


# ==================================================
# 4. 음성파일 검사 함수
# ==================================================

def is_valid_audio_file(file_path):
    """
    음성파일이 실제로 존재하고,
    최소 크기 이상인지 검사합니다.
    """

    if not os.path.isfile(file_path):
        return False

    file_size = os.path.getsize(file_path)

    return file_size >= MIN_AUDIO_SIZE


# ==================================================
# 5. 파일 삭제 함수
# ==================================================

def remove_file_if_exists(file_path):
    """
    파일이 존재할 경우 안전하게 삭제합니다.
    """

    if os.path.exists(file_path):
        try:
            os.remove(file_path)

        except OSError as error:
            print(f"파일 삭제 실패: {file_path}")
            print(f"원인: {error}")


def is_question_mark_only(value):
    """
    값 전체가 물음표로만 이루어졌는지 검사합니다.
    정상 문장 안의 물음표는 허용하고, 손상된 값만 걸러냅니다.
    """

    if value is None:
        return False

    text = str(value).strip()

    if not text:
        return False

    return bool(QUESTION_MARK_ONLY_PATTERN.fullmatch(text))


def find_corrupted_word_entries(words):
    """
    word / hiragana / meaning 필드가 물음표로만 깨진 항목을 찾습니다.
    """

    corrupted_items = []

    for index, item in enumerate(words, start=1):
        word = str(item.get("word", "")).strip()
        hiragana = str(item.get("hiragana", "")).strip()
        meaning = str(item.get("meaning", "")).strip()
        romaji = str(item.get("romaji", "")).strip()
        item_type = str(item.get("type", "")).strip()

        for field_name, field_value in (
            ("word", word),
            ("hiragana", hiragana),
            ("meaning", meaning),
        ):
            if is_question_mark_only(field_value):
                corrupted_items.append({
                    "index": index,
                    "type": item_type or "unknown",
                    "romaji": romaji or "(empty)",
                    "field": field_name,
                    "value": field_value,
                })

    return corrupted_items


def raise_if_corrupted_words(words):
    corrupted_items = find_corrupted_word_entries(words)

    if not corrupted_items:
        return

    print("깨진 데이터가 발견되어 TTS 생성을 중단합니다.")

    for item in corrupted_items:
        print(
            f"- #{item['index']} | type={item['type']} | "
            f"romaji={item['romaji']} | field={item['field']} | "
            f"value={item['value']}"
        )

    raise ValueError(
        "words.json에 물음표로만 깨진 항목이 있어 TTS를 중단했습니다."
    )


# ==================================================
# 6. 공통 TTS 생성 함수
# ==================================================

async def create_tts(text, voice, save_path):
    """
    TTS를 임시파일로 생성한 다음,
    정상 파일인 것이 확인되면 최종 MP3로 이동합니다.
    """

    if not text or not text.strip():
        raise ValueError(
            f"TTS 생성 텍스트가 비어 있습니다: {save_path}"
        )

    text = text.strip()
    save_path = str(save_path)

    # 확장자가 MP3로 끝나도록 임시파일을 만듭니다.
    temp_path = f"{save_path}.part.mp3"

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):

        # 이전 실행에서 남은 손상 파일을 삭제합니다.
        remove_file_if_exists(temp_path)
        remove_file_if_exists(save_path)

        try:
            print(
                f"TTS 생성 시도 "
                f"{attempt}/{MAX_RETRIES}: {save_path}"
            )

            communicator = edge_tts.Communicate(
                text=text,
                voice=voice,
                rate="-15%"
            )

            # 먼저 임시파일에 저장합니다.
            await communicator.save(temp_path)

            # 파일이 정상적으로 생성됐는지 검사합니다.
            if not is_valid_audio_file(temp_path):
                file_size = (
                    os.path.getsize(temp_path)
                    if os.path.exists(temp_path)
                    else 0
                )

                raise RuntimeError(
                    f"생성된 음성파일이 비정상입니다. "
                    f"파일 크기: {file_size} bytes"
                )

            # 정상적인 경우에만 최종 파일명으로 변경합니다.
            os.replace(temp_path, save_path)

            final_size = os.path.getsize(save_path)

            print(
                f"TTS 생성 성공: {save_path} "
                f"({final_size} bytes)"
            )

            return save_path

        except Exception as error:
            last_error = error

            print(
                f"TTS 생성 실패 "
                f"{attempt}/{MAX_RETRIES}: {save_path}"
            )
            print(f"원인: {error}")

            # 실패하면서 남은 불완전한 파일을 제거합니다.
            remove_file_if_exists(temp_path)

            if os.path.exists(save_path):
                if not is_valid_audio_file(save_path):
                    remove_file_if_exists(save_path)

            # 마지막 시도가 아니라면 잠시 기다렸다 재시도합니다.
            if attempt < MAX_RETRIES:
                wait_seconds = attempt * 2

                print(
                    f"{wait_seconds}초 후 다시 시도합니다."
                )

                await asyncio.sleep(wait_seconds)

    # 세 번 모두 실패하면 영상 생성 단계로 넘어가지 않습니다.
    raise RuntimeError(
        f"TTS 생성에 최종 실패했습니다: {save_path}\n"
        f"마지막 오류: {last_error}"
    )


# ==================================================
# 7. 일본어 음성 생성 함수
# ==================================================

async def create_japanese_tts(text, filename):
    save_path = os.path.join(AUDIO_FOLDER, filename)

    return await create_tts(
        text=text,
        voice=JAPANESE_VOICE,
        save_path=save_path
    )


# ==================================================
# 8. 한국어 음성 생성 함수
# ==================================================

async def create_korean_tts(text, filename):
    save_path = os.path.join(AUDIO_FOLDER, filename)

    return await create_tts(
        text=text,
        voice=KOREAN_VOICE,
        save_path=save_path
    )


# ==================================================
# 9. 단어 데이터 불러오기 함수
# ==================================================

def load_words():
    try:
        with open(
            "data/words.json",
            "r",
            encoding="utf-8"
        ) as files:
            return json.load(files)

    except FileNotFoundError:
        print("data/words.json 파일을 찾을 수 없습니다.")
        return []

    except json.JSONDecodeError as error:
        print("words.json 파일 형식이 올바르지 않습니다.")
        print(f"원인: {error}")
        return []


# ==================================================
# 10. 단어별 TTS 생성 처리 섹션
# ==================================================

async def generate_tts_from_words():
    words = load_words()

    if not words:
        print("처리할 단어 데이터가 없습니다.")
        return

    raise_if_corrupted_words(words)

    total_count = len(words)

    for index, item in enumerate(words, start=1):
        word = str(item.get("word", "")).strip()
        hiragana = str(item.get("hiragana", "")).strip()
        meaning = str(item.get("meaning", "")).strip()
        romaji = str(item.get("romaji", "")).strip()

        print("")
        print("=" * 50)
        print(f"TTS 처리: {index}/{total_count}")
        print(f"단어: {word}")
        print(f"히라가나: {hiragana}")
        print(f"뜻: {meaning}")
        print("=" * 50)

        if not romaji:
            raise ValueError(
                f"{word}의 romaji 값이 비어 있습니다."
            )

        if not hiragana:
            raise ValueError(
                f"{word}의 hiragana 값이 비어 있습니다."
            )

        if not meaning:
            raise ValueError(
                f"{word}의 meaning 값이 비어 있습니다."
            )

        safe_romaji = normalize_romaji_filename(romaji)

        jp_filename = f"{safe_romaji}_jp.mp3"
        kr_filename = f"{safe_romaji}_kr.mp3"

        jp_path = await create_japanese_tts(
            hiragana,
            jp_filename
        )

        kr_path = await create_korean_tts(
            meaning,
            kr_filename
        )

        print("")
        print("단어 TTS 생성 완료")
        print(f"일본어: {jp_path}")
        print(f"한국어: {kr_path}")

    print("")
    print("=" * 50)
    print("전체 TTS 음성 생성 완료")
    print("=" * 50)


# ==================================================
# 11. 테스트 실행 섹션
# ==================================================

async def test():
    await generate_tts_from_words()


if __name__ == "__main__":
    asyncio.run(test())
