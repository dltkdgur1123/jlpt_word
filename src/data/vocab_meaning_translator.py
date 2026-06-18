# ==================================================
# 파일명: vocab_meaning_translator.py
# 역할: JLPT 단어 CSV의 영어 뜻을 한국어 뜻으로 자동 변환하는 도구
# ==================================================


# ==================================================
# 1. 라이브러리 import 섹션
# ==================================================

import csv
import json
import os
import time

from deep_translator import GoogleTranslator


# ==================================================
# 2. 기본 설정 섹션
# ==================================================

DATA_FOLDER = "data"

CACHE_FILE = os.path.join(
    DATA_FOLDER,
    "translation_cache.json"
)

VOCAB_CSV_FILES = [
    "data/jlpt_n1_vocab.csv",
    "data/jlpt_n2_vocab.csv",
    "data/jlpt_n3_vocab.csv",
    "data/jlpt_n4_vocab.csv",
    "data/jlpt_n5_vocab.csv"
]

CSV_FIELDNAMES = [
    "word",
    "hiragana",
    "meaning",
    "romaji",
    "score",
    "used",
    "day"
]


# ==================================================
# 3. 번역 캐시 불러오기 함수 섹션
# ==================================================

def load_translation_cache():
    if not os.path.exists(CACHE_FILE):
        return {}

    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as file:
            cache = json.load(file)

        return cache

    except json.JSONDecodeError:
        return {}


# ==================================================
# 4. 번역 캐시 저장 함수 섹션
# ==================================================

def save_translation_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as file:
        json.dump(
            cache,
            file,
            ensure_ascii=False,
            indent=4
        )


# ==================================================
# 5. 한국어 여부 확인 함수 섹션
# ==================================================

def is_probably_korean(text):
    for char in text:
        if "가" <= char <= "힣":
            return True

    return False


# ==================================================
# 6. 뜻 번역 함수 섹션
# ==================================================

def translate_meaning(meaning, cache):
    meaning = meaning.strip()

    if not meaning:
        return ""

    if is_probably_korean(meaning):
        return meaning

    if meaning in cache:
        return cache[meaning]

    try:
        translated = GoogleTranslator(
            source="en",
            target="ko"
        ).translate(meaning)

        cache[meaning] = translated

        time.sleep(0.25)

        return translated

    except Exception as error:
        print("번역 실패:", meaning)
        print(error)

        return meaning


# ==================================================
# 7. CSV 행 불러오기 함수 섹션
# ==================================================

def load_csv_rows(csv_path):
    rows = []

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            rows.append({
                "word": row.get("word", "").strip(),
                "hiragana": row.get("hiragana", "").strip(),
                "meaning": row.get("meaning", "").strip(),
                "romaji": row.get("romaji", "").strip(),
                "score": row.get("score", "50").strip(),
                "used": row.get("used", "false").strip(),
                "day": row.get("day", "").strip()
            })

    return rows


# ==================================================
# 8. CSV 행 저장 함수 섹션
# ==================================================

def save_csv_rows(csv_path, rows):
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=CSV_FIELDNAMES
        )

        writer.writeheader()

        for row in rows:
            writer.writerow(row)


# ==================================================
# 9. 단일 CSV 번역 함수 섹션
# ==================================================

def translate_vocab_csv(csv_path):
    if not os.path.exists(csv_path):
        print("파일 없음:", csv_path)
        return

    print("=" * 60)
    print("번역 시작:", csv_path)
    print("=" * 60)

    cache = load_translation_cache()

    rows = load_csv_rows(csv_path)

    total_count = len(rows)
    translated_count = 0
    skipped_count = 0

    for index, row in enumerate(rows, start=1):
        original_meaning = row.get("meaning", "")

        if is_probably_korean(original_meaning):
            skipped_count = skipped_count + 1
            continue

        korean_meaning = translate_meaning(
            original_meaning,
            cache
        )

        row["meaning"] = clean_meaning_text(korean_meaning)

        translated_count = translated_count + 1

        if index % 20 == 0:
            save_translation_cache(cache)
            save_csv_rows(csv_path, rows)

            print(
                "진행 중:",
                csv_path,
                index,
                "/",
                total_count
            )

    save_translation_cache(cache)
    save_csv_rows(csv_path, rows)

    print("완료:", csv_path)
    print("전체:", total_count)
    print("번역:", translated_count)
    print("건너뜀:", skipped_count)


# ==================================================
# 10. 전체 단어 CSV 번역 함수 섹션
# ==================================================

def translate_all_vocab_csv():
    for csv_path in VOCAB_CSV_FILES:
        translate_vocab_csv(csv_path)

    print("전체 단어 뜻 한국어 변환 완료")


# ==================================================
# 11. 특수 문자 제거
# ==================================================

def clean_meaning_text(text):
    text = str(text).strip()

    remove_chars = [
        "□",
        "■",
        "●",
        "○",
        "◆",
        "◇",
        "※",
        "・",
        "•",
        "▶",
        "▷"
    ]

    for char in remove_chars:
        text = text.replace(char, "")

    text = text.replace("；", ",")
    text = text.replace(";", ",")
    text = text.replace("、", ",")

    parts = []

    for part in text.split(","):
        part = part.strip()

        if not part:
            continue

        if part not in parts:
            parts.append(part)

    return ", ".join(parts)


# ==================================================
# 12. 테스트 실행 섹션
# ==================================================

if __name__ == "__main__":
    translate_all_vocab_csv()