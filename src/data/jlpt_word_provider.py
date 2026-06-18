# ==================================================
# 파일명: jlpt_word_provider.py
# 역할: 레벨별 단어 CSV와 문법 CSV에서 아직 사용하지 않은 항목을 골라 words.json에 추가하는 모듈
# ==================================================


# ==================================================
# 1. 라이브러리 import 섹션
# ==================================================

import csv
import os

from src.data.word_manager import add_word, clear_words
from src.data.day_manager import get_current_day_text


# ==================================================
# 2. 기본 설정 섹션
# ==================================================

# 하루에 추가할 단어 개수
VOCAB_COUNT = 5

# 하루에 추가할 문법 개수
GRAMMAR_COUNT = 2

# CSV 컬럼 순서
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
# 3. 레벨별 CSV 파일 경로 생성 함수 섹션
# ==================================================

# - JLPT 레벨을 받는다.
# - 예: "N1", "N2", "N3", "N4", "N5"
# - 해당 레벨의 단어 CSV 파일 경로를 만든다.


def get_vocab_csv_file(level):
    vocab_csv_file = os.path.join(
        "data",
        f"jlpt_{level.lower()}_vocab.csv"
    )

    return vocab_csv_file


# - JLPT 레벨을 받는다.
# - 해당 레벨의 문법 CSV 파일 경로를 만든다.


def get_grammar_csv_file(level):
    grammar_csv_file = os.path.join(
        "data",
        f"jlpt_{level.lower()}_grammar.csv"
    )

    return grammar_csv_file


# ==================================================
# 4. CSV 파일 불러오기 함수 섹션
# ==================================================

# - CSV 파일 경로를 받는다.
# - vocab 또는 grammar 타입을 받는다.
# - CSV 파일을 읽는다.
# - word, hiragana, meaning, romaji, score, used, day 값을 꺼낸다.
# - 값이 부족한 행은 건너뛴다.
# - 각 항목에 type 값을 붙여서 반환한다.


def load_csv_file(csv_file, item_type):
    if not os.path.exists(csv_file):
        print("CSV 파일을 찾을 수 없습니다:", csv_file)
        return []

    items = []

    try:
        with open(csv_file, "r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)

            for row in reader:
                word = (row.get("word") or "").strip()
                hiragana = (row.get("hiragana") or "").strip()
                meaning = (row.get("meaning") or "").strip()
                romaji = (row.get("romaji") or "").strip()
                score = (row.get("score") or "0").strip()
                used = (row.get("used") or "false").strip()
                day = (row.get("day") or "").strip()

                if not word or not hiragana or not meaning or not romaji:
                    continue

                item = {
                    "type": item_type,
                    "word": word,
                    "hiragana": hiragana,
                    "meaning": meaning,
                    "romaji": romaji,
                    "score": int(score) if score.isdigit() else 0,
                    "used": used,
                    "day": day
                }

                items.append(item)

        return items

    except Exception as error:
        print("CSV 파일을 읽는 중 오류가 발생했습니다:", csv_file)
        print(error)
        return []


# ==================================================
# 5. CSV 파일 저장 함수 섹션
# ==================================================

# - CSV 파일 경로를 받는다.
# - 저장할 항목 목록을 받는다.
# - used, day 상태가 반영된 데이터를 다시 저장한다.
# - type은 파일 자체가 단어/문법을 구분하므로 저장하지 않는다.


def save_csv_items(csv_file, items):
    try:
        with open(csv_file, "w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=CSV_FIELDNAMES
            )

            writer.writeheader()

            for item in items:
                writer.writerow({
                    "word": item.get("word", ""),
                    "hiragana": item.get("hiragana", ""),
                    "meaning": item.get("meaning", ""),
                    "romaji": item.get("romaji", ""),
                    "score": item.get("score", 0),
                    "used": item.get("used", "false"),
                    "day": item.get("day", "")
                })

        print("CSV 사용 상태 저장 완료:", csv_file)

    except Exception as error:
        print("CSV 파일을 저장하는 중 오류가 발생했습니다:", csv_file)
        print(error)


# ==================================================
# 6. 미사용 항목 필터 함수 섹션
# ==================================================

# - 전체 후보 목록을 받는다.
# - used가 true가 아닌 데이터만 고른다.
# - score가 높은 순서대로 정렬한다.


def filter_unused_items(items):
    filtered_items = []

    for item in items:
        used = item.get("used", "false").lower()

        if used != "true":
            filtered_items.append(item)

    filtered_items.sort(
        key=lambda item: item.get("score", 0),
        reverse=True
    )

    return filtered_items


# ==================================================
# 7. words.json 등록 함수 섹션
# ==================================================

# - 후보 아이템 1개를 받는다.
# - type, word, hiragana, meaning, romaji 값을 꺼낸다.
# - word_manager.py의 add_word 함수로 words.json에 추가한다.
# - 추가 성공 여부를 반환한다.


def add_item_to_words(item, level="N1"):
    item_type = item.get("type", "vocab")
    word = item.get("word", "")
    hiragana = item.get("hiragana", "")
    meaning = item.get("meaning", "")
    romaji = item.get("romaji", "")

    result = add_word(
        word,
        hiragana,
        meaning,
        romaji,
        item_type,
        level
    )

    return result


# ==================================================
# 8. 지정 개수만큼 항목 등록 함수 섹션
# ==================================================

# - 후보 목록을 받는다.
# - 지정 개수를 받는다.
# - 현재 DAY 텍스트를 받는다.
# - 지정 개수만큼 words.json에 추가한다.
# - words.json에 이미 있더라도 used=true, day=현재 DAY로 처리한다.
# - 실제 새로 추가된 개수를 반환한다.


def add_items(items, count, current_day, level):
    success_count = 0

    for item in items:
        if success_count >= count:
            break

        is_added = add_item_to_words(item, level)

        item["used"] = "true"
        item["day"] = current_day

        if is_added:
            success_count = success_count + 1

    return success_count


# ==================================================
# 9. 레벨별 오늘의 콘텐츠 추가 함수 섹션
# ==================================================

# - JLPT 레벨을 받는다.
# - 해당 레벨의 단어 CSV에서 미사용 단어를 불러온다.
# - 해당 레벨의 문법 CSV에서 미사용 문법을 불러온다.
# - 단어와 문법을 words.json에 추가한다.
# - 선택된 항목은 각 CSV에 used=true, day=현재 DAY로 저장한다.


def add_daily_items(level="N1"):
    clear_words()

    current_day = get_current_day_text(level)

    vocab_csv_file = get_vocab_csv_file(level)
    grammar_csv_file = get_grammar_csv_file(level)

    vocab_items = load_csv_file(
        vocab_csv_file,
        "vocab"
    )

    grammar_items = load_csv_file(
        grammar_csv_file,
        "grammar"
    )

    if not vocab_items and not grammar_items:
        print(level, "CSV에서 가져올 데이터가 없습니다.")
        return

    unused_vocab_items = filter_unused_items(vocab_items)
    unused_grammar_items = filter_unused_items(grammar_items)

    unused_vocab_items.sort(
        key=lambda x: int(x.get("score", 50)),
        reverse=True
    )

    unused_grammar_items.sort(
        key=lambda x: int(x.get("score", 50)),
        reverse=True
    )

    print(level, "미사용 단어 후보 수:", len(unused_vocab_items))
    print(level, "미사용 문법 후보 수:", len(unused_grammar_items))

    added_vocab_count = add_items(
        unused_vocab_items,
        VOCAB_COUNT,
        current_day,
        level
    )

    added_grammar_count = add_items(
        unused_grammar_items,
        GRAMMAR_COUNT,
        current_day,
        level
    )

    save_csv_items(
        vocab_csv_file,
        vocab_items
    )

    save_csv_items(
        grammar_csv_file,
        grammar_items
    )

    print(level, "오늘 콘텐츠 추가 완료")
    print("단어:", added_vocab_count, "개")
    print("문법:", added_grammar_count, "개")


# ==================================================
# 10. 테스트 실행 섹션
# ==================================================

if __name__ == "__main__":
    add_daily_items("N1")