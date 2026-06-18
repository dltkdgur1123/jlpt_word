# ==================================================
# 파일명: frequency_score_builder.py
# 역할: source_data.csv를 기준으로 JLPT 단어/문법 CSV의 score를 갱신하는 도구
# ==================================================

import csv
import os


# ==================================================
# 1. 기본 설정 섹션
# ==================================================

DATA_FOLDER = "data"

SOURCE_DATA_FILE = os.path.join(
    DATA_FOLDER,
    "source_data.csv"
)

TARGET_CSV_FILES = [
    "data/jlpt_n1_vocab.csv",
    "data/jlpt_n2_vocab.csv",
    "data/jlpt_n3_vocab.csv",
    "data/jlpt_n4_vocab.csv",
    "data/jlpt_n5_vocab.csv",

    "data/jlpt_n1_grammar.csv",
    "data/jlpt_n2_grammar.csv",
    "data/jlpt_n3_grammar.csv",
    "data/jlpt_n4_grammar.csv",
    "data/jlpt_n5_grammar.csv",
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
# 2. 텍스트 정리 함수 섹션
# ==================================================

def clean_text(text):
    if not text:
        return ""

    text = str(text).strip()
    text = text.replace("~", "～")
    text = text.replace("〜", "～")

    return text

def normalize_match_key(text):
    text = clean_text(text)

    text = text.replace("～", "")
    text = text.replace("~", "")
    text = text.replace("〜", "")

    return text


# ==================================================
# 3. source_data.csv 불러오기 섹션
# ==================================================

def load_source_data():
    source_rows = []

    if not os.path.exists(SOURCE_DATA_FILE):
        print("source_data.csv 파일 없음:", SOURCE_DATA_FILE)
        return source_rows

    with open(
        SOURCE_DATA_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            item = clean_text(row.get("item", ""))
            item_type = clean_text(row.get("type", ""))
            level = clean_text(row.get("level", ""))
            source = clean_text(row.get("source", ""))

            if not item:
                continue

            source_rows.append({
                "item": item,
                "type": item_type,
                "level": level,
                "source": source
            })

    return source_rows


# ==================================================
# 4. 빈도 딕셔너리 생성 섹션
# ==================================================

def build_frequency_dict(source_rows):
    frequency_dict = {}

    for row in source_rows:
        item = normalize_match_key(
        row.get("item", "")
    )

        if not item:
            continue

        frequency_dict[item] = frequency_dict.get(item, 0) + 1

    return frequency_dict


# ==================================================
# 5. score 계산 함수 섹션
# ==================================================

def calculate_score(frequency):
    base_score = 50

    added_score = frequency * 10

    score = base_score + added_score

    if score > 100:
        score = 100

    return score


# ==================================================
# 6. CSV 불러오기 섹션
# ==================================================

def load_target_csv(csv_path):
    rows = []

    if not os.path.exists(csv_path):
        print("대상 CSV 없음:", csv_path)
        return rows

    with open(
        csv_path,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            rows.append({
                "word": clean_text(row.get("word", "")),
                "hiragana": clean_text(row.get("hiragana", "")),
                "meaning": clean_text(row.get("meaning", "")),
                "romaji": clean_text(row.get("romaji", "")),
                "score": clean_text(row.get("score", "50")),
                "used": clean_text(row.get("used", "false")),
                "day": clean_text(row.get("day", "")),
            })

    return rows


# ==================================================
# 7. CSV 저장 섹션
# ==================================================

def save_target_csv(csv_path, rows):
    with open(
        csv_path,
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=CSV_FIELDNAMES
        )

        writer.writeheader()

        for row in rows:
            writer.writerow(row)


# ==================================================
# 8. 단일 CSV score 갱신 섹션
# ==================================================

def update_score_for_csv(csv_path, frequency_dict):
    rows = load_target_csv(csv_path)

    if not rows:
        return

    updated_count = 0

    for row in rows:
        word = normalize_match_key(
            row.get("word", "")
        )

        frequency = frequency_dict.get(word, 0)

        if frequency > 0:
            row["score"] = str(
                calculate_score(frequency)
            )
            updated_count += 1
        else:
            row["score"] = row.get("score", "50") or "50"

    save_target_csv(csv_path, rows)

    print(
        "score 갱신 완료:",
        csv_path,
        "/ 반영:",
        updated_count,
        "개"
    )


# ==================================================
# 9. 전체 CSV score 갱신 섹션
# ==================================================

def update_all_scores():
    source_rows = load_source_data()

    print("source_data 수:", len(source_rows))

    frequency_dict = build_frequency_dict(source_rows)

    print("빈도 항목 수:", len(frequency_dict))

    for csv_path in TARGET_CSV_FILES:
        update_score_for_csv(
            csv_path,
            frequency_dict
        )

    print("전체 score 갱신 완료")


# ==================================================
# 10. 테스트 실행 섹션
# ==================================================

if __name__ == "__main__":
    update_all_scores()