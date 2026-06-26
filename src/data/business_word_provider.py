import csv
import os

from src.data.day_manager import get_current_day_text
from src.data.word_manager import add_word, clear_words

VOCAB_COUNT = 3
PHRASE_COUNT = 4
BUSINESS_LEVEL = "BUSINESS"

CSV_FIELDNAMES = [
    "word",
    "hiragana",
    "meaning",
    "romaji",
    "score",
    "used",
    "day",
]

BUSINESS_VOCAB_FILE = os.path.join("data", "business_japanese_vocab.csv")
BUSINESS_PHRASES_FILE = os.path.join("data", "business_japanese_phrases.csv")


def load_csv_file(csv_file, item_type):
    if not os.path.exists(csv_file):
        print("CSV file not found:", csv_file)
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

                items.append({
                    "type": item_type,
                    "word": word,
                    "hiragana": hiragana,
                    "meaning": meaning,
                    "romaji": romaji,
                    "score": int(score) if score.isdigit() else 0,
                    "used": used,
                    "day": day,
                })

    except Exception as error:
        print("Failed to read CSV:", csv_file)
        print(error)
        return []

    return items


def save_csv_items(csv_file, items):
    with open(csv_file, "w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()

        for item in items:
            writer.writerow({
                "word": item.get("word", ""),
                "hiragana": item.get("hiragana", ""),
                "meaning": item.get("meaning", ""),
                "romaji": item.get("romaji", ""),
                "score": item.get("score", 0),
                "used": item.get("used", "false"),
                "day": item.get("day", ""),
            })

    print("Saved CSV status:", csv_file)


def filter_unused_items(items):
    filtered_items = []

    for item in items:
        if item.get("used", "false").lower() != "true":
            filtered_items.append(item)

    filtered_items.sort(key=lambda item: item.get("score", 0), reverse=True)
    return filtered_items


def add_item_to_words(item, level=BUSINESS_LEVEL):
    return add_word(
        item.get("word", ""),
        item.get("hiragana", ""),
        item.get("meaning", ""),
        item.get("romaji", ""),
        item.get("type", "business_vocab"),
        level,
    )


def add_items(items, count, current_day, level=BUSINESS_LEVEL):
    success_count = 0

    for item in items:
        if success_count >= count:
            break

        is_added = add_item_to_words(item, level)
        item["used"] = "true"
        item["day"] = current_day

        if is_added:
            success_count += 1

    return success_count


def add_daily_business_items(level=BUSINESS_LEVEL):
    level = BUSINESS_LEVEL
    clear_words()

    current_day = get_current_day_text(level)

    vocab_items = load_csv_file(BUSINESS_VOCAB_FILE, "business_vocab")
    phrase_items = load_csv_file(BUSINESS_PHRASES_FILE, "business_phrase")

    if not vocab_items and not phrase_items:
        print(level, "No business data available.")
        return

    unused_vocab_items = filter_unused_items(vocab_items)
    unused_phrase_items = filter_unused_items(phrase_items)

    print(level, "unused vocab:", len(unused_vocab_items))
    print(level, "unused phrases:", len(unused_phrase_items))

    added_vocab_count = add_items(unused_vocab_items, VOCAB_COUNT, current_day, level)
    added_phrase_count = add_items(unused_phrase_items, PHRASE_COUNT, current_day, level)

    save_csv_items(BUSINESS_VOCAB_FILE, vocab_items)
    save_csv_items(BUSINESS_PHRASES_FILE, phrase_items)

    print(level, "added vocab:", added_vocab_count)
    print(level, "added phrases:", added_phrase_count)


if __name__ == "__main__":
    add_daily_business_items()
