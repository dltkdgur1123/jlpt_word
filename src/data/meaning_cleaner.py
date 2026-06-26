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


def normalize_row_keys(row):
    normalized = {}

    for key, value in row.items():
        clean_key = str(key).replace("﻿", "").strip()
        normalized[clean_key] = value

    return normalized


def clean_meaning_text(text):
    text = str(text).strip()

    remove_chars = [
        "?", "?", "?", "?", "?", "?",
        "?", "?", "?", "?", "?",
    ]

    for char in remove_chars:
        text = text.replace(char, "")

    text = text.replace("?", ",")
    text = text.replace(";", ",")
    text = text.replace("?", ",")

    text = re.sub(r"\s+", " ", text)
    text = text.replace(" ", " ")
    text = text.replace("​", "")
    text = text.replace("﻿", "")
    text = re.sub(r"\s+", " ", text)
    text = text.replace("?:  ", "?: ")

    parts = []
    seen = set()

    for part in text.split(","):
        part = part.strip()

        if not part or part in seen:
            continue

        seen.add(part)
        parts.append(part)

    return ", ".join(parts)


def clean_csv(csv_path):
    if not os.path.exists(csv_path):
        print("?? ??:", csv_path)
        return

    rows = []
    changed_count = 0

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            row = normalize_row_keys(row)

            old_meaning = row.get("meaning", "")
            new_meaning = clean_meaning_text(old_meaning)

            if old_meaning != new_meaning:
                changed_count += 1

            cleaned_row = {field: row.get(field, "") for field in FIELDNAMES}
            cleaned_row["meaning"] = new_meaning
            rows.append(cleaned_row)

    with open(csv_path, "w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(csv_path, "?? ?? / ??:", changed_count, "?")


def clean_all():
    for csv_path in CSV_FILES:
        clean_csv(csv_path)

    print("?? meaning ?? ??")


if __name__ == "__main__":
    clean_all()
