# ==================================================
# 파일명: vocab_data_builder.py
# 역할: 공개 JLPT 단어 CSV를 다운로드해서 프로젝트용 vocab CSV로 변환하는 모듈
# ==================================================


# ==================================================
# 1. 라이브러리 import 섹션
# ==================================================

import csv
import os
import requests

from pykakasi import kakasi


# ==================================================
# 2. 기본 설정 섹션
# ==================================================

DATA_FOLDER = "data"

RAW_DATA_FOLDER = os.path.join(
    DATA_FOLDER,
    "raw_vocab"
)

JLPT_LEVELS = [
    "N1",
    "N2",
    "N3",
    "N4",
    "N5"
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

SOURCE_URLS = {
    "N1": "https://raw.githubusercontent.com/jamsinclair/open-anki-jlpt-decks/main/src/n1.csv",
    "N2": "https://raw.githubusercontent.com/jamsinclair/open-anki-jlpt-decks/main/src/n2.csv",
    "N3": "https://raw.githubusercontent.com/jamsinclair/open-anki-jlpt-decks/main/src/n3.csv",
    "N4": "https://raw.githubusercontent.com/jamsinclair/open-anki-jlpt-decks/main/src/n4.csv",
    "N5": "https://raw.githubusercontent.com/jamsinclair/open-anki-jlpt-decks/main/src/n5.csv",
}


# ==================================================
# 3. 폴더 생성 함수 섹션
# ==================================================

def ensure_folders():
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)

    if not os.path.exists(RAW_DATA_FOLDER):
        os.makedirs(RAW_DATA_FOLDER)


# ==================================================
# 4. 원본 CSV 다운로드 함수 섹션
# ==================================================

def download_raw_csv(level):
    url = SOURCE_URLS.get(level)

    if not url:
        print("지원하지 않는 레벨입니다:", level)
        return ""

    save_path = os.path.join(
        RAW_DATA_FOLDER,
        f"{level.lower()}_raw.csv"
    )

    try:
        response = requests.get(
            url,
            timeout=30
        )

        response.raise_for_status()

        with open(save_path, "w", encoding="utf-8-sig", newline="") as file:
            file.write(response.text)

        print(level, "원본 CSV 다운로드 완료:", save_path)

        return save_path

    except Exception as error:
        print(level, "원본 CSV 다운로드 실패")
        print(error)

        return ""


# ==================================================
# 5. 원본 CSV 행 분석 함수 섹션
# ==================================================

def guess_column_value(row, possible_names):
    for name in possible_names:
        if name in row and row.get(name):
            return row.get(name, "").strip()

    return ""


def convert_raw_row(row):
    word = guess_column_value(
        row,
        [
            "expression",
            "word",
            "kanji",
            "Japanese",
            "japanese",
            "term"
        ]
    )

    hiragana = guess_column_value(
        row,
        [
            "reading",
            "hiragana",
            "kana",
            "furigana"
        ]
    )

    meaning = guess_column_value(
        row,
        [
            "meaning",
            "Meaning",
            "english",
            "English",
            "gloss",
            "definition"
        ]
    )

    romaji = guess_column_value(
        row,
        [
            "romaji",
            "Romaji"
        ]
    )

    if not word:
        return None

    if not hiragana:
        hiragana = word

    if not meaning:
        meaning = ""

    if not romaji:
        romaji = hiragana_to_romaji(hiragana)

    converted_row = {
        "word": word,
        "hiragana": hiragana,
        "meaning": meaning,
        "romaji": romaji,
        "score": 50,
        "used": "false",
        "day": ""
    }

    return converted_row


# ==================================================
# 6. 임시 romaji 키 생성 함수 섹션
# ==================================================

def hiragana_to_romaji(text):
    try:
        kks = kakasi()

        result = kks.convert(text)

        romaji = ""

        for item in result:
            romaji += item["hepburn"]

        romaji = romaji.lower()

        romaji = romaji.replace(" ", "_")
        romaji = romaji.replace("-", "_")

        return romaji

    except Exception:
        return "unknown"


# ==================================================
# 7. 중복 romaji 보정 함수 섹션
# ==================================================

def fix_duplicate_romaji(rows):
    used_romaji = {}
    fixed_rows = []

    for row in rows:
        romaji = row.get("romaji", "item")

        if romaji not in used_romaji:
            used_romaji[romaji] = 1
            fixed_rows.append(row)
            continue

        used_romaji[romaji] = used_romaji[romaji] + 1

        row["romaji"] = f"{romaji}_{used_romaji[romaji]}"

        fixed_rows.append(row)

    return fixed_rows


# ==================================================
# 8. 원본 CSV 변환 함수 섹션
# ==================================================

def convert_raw_csv(level, raw_csv_path):
    if not raw_csv_path:
        print(level, "원본 CSV 경로가 없습니다.")
        return []

    converted_rows = []

    try:
        with open(raw_csv_path, "r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)

            for row in reader:
                converted_row = convert_raw_row(row)

                if not converted_row:
                    continue

                converted_rows.append(converted_row)

        converted_rows = fix_duplicate_romaji(converted_rows)

        print(level, "변환 완료:", len(converted_rows), "개")

        return converted_rows

    except Exception as error:
        print(level, "CSV 변환 중 오류 발생")
        print(error)

        return []


# ==================================================
# 9. 프로젝트용 CSV 저장 함수 섹션
# ==================================================

def save_project_vocab_csv(level, rows):
    save_path = os.path.join(
        DATA_FOLDER,
        f"jlpt_{level.lower()}_vocab.csv"
    )

    try:
        with open(save_path, "w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=CSV_FIELDNAMES
            )

            writer.writeheader()

            for row in rows:
                writer.writerow(row)

        print(level, "프로젝트용 vocab CSV 저장 완료:", save_path)

        return save_path

    except Exception as error:
        print(level, "프로젝트용 CSV 저장 실패")
        print(error)

        return ""


# ==================================================
# 10. 레벨별 전체 처리 함수 섹션
# ==================================================

def build_vocab_csv_for_level(level):
    raw_csv_path = download_raw_csv(level)

    rows = convert_raw_csv(
        level,
        raw_csv_path
    )

    if not rows:
        print(level, "저장할 데이터가 없습니다.")
        return ""

    save_path = save_project_vocab_csv(
        level,
        rows
    )

    return save_path


# ==================================================
# 11. 전체 레벨 처리 함수 섹션
# ==================================================

def build_all_vocab_csv():
    ensure_folders()

    for level in JLPT_LEVELS:
        print("===================================")
        print(level, "단어 CSV 생성 시작")
        print("===================================")

        build_vocab_csv_for_level(level)

    print("전체 단어 CSV 생성 완료")


# ==================================================
# 12. 테스트 실행 섹션
# ==================================================

if __name__ == "__main__":
    build_all_vocab_csv()