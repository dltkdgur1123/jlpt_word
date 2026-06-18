# ==================================================
# 파일명: csv_validator.py
# 역할: JLPT CSV 데이터 검증 도구
# ==================================================

import csv
import os


# ==================================================
# 검사 대상 파일
# ==================================================

CSV_FILES = [
    "data/jlpt_n1_vocab.csv",
    "data/jlpt_n1_grammar.csv",
    "data/jlpt_n2_vocab.csv",
    "data/jlpt_n2_grammar.csv",
    "data/jlpt_n3_vocab.csv",
    "data/jlpt_n3_grammar.csv",
    "data/jlpt_n4_vocab.csv",
    "data/jlpt_n4_grammar.csv",
    "data/jlpt_n5_vocab.csv",
    "data/jlpt_n5_grammar.csv",
]


# ==================================================
# CSV 검사
# ==================================================

def validate_csv(csv_path):
    print("\n" + "=" * 60)
    print("검사 파일:", csv_path)
    print("=" * 60)

    if not os.path.exists(csv_path):
        print("파일 없음")
        return

    romaji_set = set()

    total_rows = 0
    duplicate_romaji = 0
    empty_word = 0
    empty_meaning = 0
    invalid_used = 0

    with open(csv_path, "r", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        for row in reader:
            total_rows += 1

            word = row.get("word", "").strip()
            meaning = row.get("meaning", "").strip()
            romaji = row.get("romaji", "").strip()
            used = row.get("used", "").strip()

            if not word:
                empty_word += 1

            if not meaning:
                empty_meaning += 1

            if used not in ["true", "false"]:
                invalid_used += 1

            if romaji:
                if romaji in romaji_set:
                    duplicate_romaji += 1
                else:
                    romaji_set.add(romaji)

    print("총 데이터 :", total_rows)
    print("빈 word :", empty_word)
    print("빈 meaning :", empty_meaning)
    print("중복 romaji :", duplicate_romaji)
    print("잘못된 used :", invalid_used)

    if (
        empty_word == 0
        and empty_meaning == 0
        and duplicate_romaji == 0
        and invalid_used == 0
    ):
        print("정상")
    else:
        print("수정 필요")


# ==================================================
# 전체 검사
# ==================================================

def validate_all():
    for csv_file in CSV_FILES:
        validate_csv(csv_file)


# ==================================================
# 테스트 실행
# ==================================================

if __name__ == "__main__":
    validate_all()