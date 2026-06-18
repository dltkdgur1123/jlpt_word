import csv
import os
import re

CSV_FILES = [
    "data/jlpt_n1_vocab.csv",
    "data/jlpt_n2_vocab.csv",
    "data/jlpt_n3_vocab.csv",
    "data/jlpt_n4_vocab.csv",
    "data/jlpt_n5_vocab.csv",
]

FIELDNAMES = [
    "word",
    "hiragana",
    "meaning",
    "romaji",
    "score",
    "used",
    "day",
]


def clean_meaning_text(text):
    text = str(text).strip()

    remove_chars = [
        "□", "■", "●", "○", "◆", "◇",
        "※", "・", "•", "▶", "▷",
    ]

    for char in remove_chars:
        text = text.replace(char, "")

    text = text.replace("；", ",")
    text = text.replace(";", ",")
    text = text.replace("、", ",")

    text = re.sub(r"\s+", " ", text)
    
    # 이상한 공백 문자 정리
    text = text.replace("\u00a0", " ")
    text = text.replace("\u200b", "")
    text = text.replace("\ufeff", "")

    # 연속 공백을 한 칸으로 정리
    text = re.sub(r"\s+", " ", text)

    # 괄호 안 콜론 뒤 공백 정리
    text = text.replace("예:  ", "예: ")

    parts = []
    seen = set()

    for part in text.split(","):
        part = part.strip()

        if not part:
            continue

        if part in seen:
            continue

        seen.add(part)
        parts.append(part)

    return ", ".join(parts)


def clean_csv(csv_path):
    if not os.path.exists(csv_path):
        print("파일 없음:", csv_path)
        return

    rows = []
    changed_count = 0

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            old_meaning = row.get("meaning", "")
            new_meaning = clean_meaning_text(old_meaning)

            if old_meaning != new_meaning:
                changed_count += 1

            row["meaning"] = new_meaning
            rows.append(row)

    with open(csv_path, "w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(csv_path, "정리 완료 / 수정:", changed_count, "개")


def clean_all():
    for csv_path in CSV_FILES:
        clean_csv(csv_path)

    print("전체 meaning 정리 완료")


if __name__ == "__main__":
    clean_all()