# ==================================================
# 파일명: jlpt_scraper.py
# 역할: JLPT Sensei에서 N1~N5 단어/문법을 크롤링하여 프로젝트용 CSV로 저장하는 모듈
# ==================================================


# ==================================================
# 1. 라이브러리 import 섹션
# ==================================================

import csv
import os
import re
import time
import json
import requests

from bs4 import BeautifulSoup
from pykakasi import kakasi

try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None


# ==================================================
# 2. 기본 설정 섹션
# ==================================================

DATA_FOLDER = "data"

CACHE_FILE = os.path.join(DATA_FOLDER, "translation_cache.json")

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

BASE_URL = "https://jlptsensei.com"

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

REQUEST_DELAY = 0.7

TRANSLATE_TO_KOREAN = True


# ==================================================
# 3. 폴더 및 캐시 준비 섹션
# ==================================================

def ensure_data_folder():
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)


def load_translation_cache():
    if not os.path.exists(CACHE_FILE):
        return {}

    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except json.JSONDecodeError:
        return {}


def save_translation_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as file:
        json.dump(
            cache,
            file,
            ensure_ascii=False,
            indent=4
        )


# ==================================================
# 4. 한국어 번역 함수 섹션
# ==================================================

def translate_to_korean(text, cache):
    if not TRANSLATE_TO_KOREAN:
        return text

    if not text:
        return ""

    if text in cache:
        return cache[text]

    if GoogleTranslator is None:
        print("deep-translator가 설치되어 있지 않아 영어 뜻을 그대로 저장합니다.")
        return text

    try:
        translated_text = GoogleTranslator(
            source="en",
            target="ko"
        ).translate(text)

        cache[text] = translated_text

        time.sleep(0.2)

        return translated_text

    except Exception as error:
        print("번역 실패:", text)
        print(error)
        return text


# ==================================================
# 5. 텍스트 정리 함수 섹션
# ==================================================

def clean_text(text):
    if not text:
        return ""

    text = text.replace("\n", " ")
    text = text.replace("\t", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def remove_number_prefix(text):
    text = clean_text(text)
    text = re.sub(r"^\d+\s*", "", text)

    return text.strip()


# ==================================================
# 6. 로마자 키 생성 함수 섹션
# ==================================================

def japanese_to_romaji(text):
    try:
        kks = kakasi()
        result = kks.convert(text)

        romaji = ""

        for item in result:
            romaji = romaji + item["hepburn"]

        return normalize_romaji_key(romaji)

    except Exception:
        return normalize_romaji_key(text)


def normalize_romaji_key(text):
    text = text.lower()
    text = text.replace("ー", "")
    text = text.replace("～", "")
    text = text.replace("〜", "")
    text = text.replace("/", "_")
    text = text.replace("-", "_")
    text = text.replace(" ", "_")

    cleaned = ""

    for char in text:
        if char.isascii() and char.isalnum():
            cleaned = cleaned + char
        else:
            cleaned = cleaned + "_"

    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")

    cleaned = cleaned.strip("_")

    if not cleaned:
        cleaned = "item"

    return cleaned


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
# 8. 페이지 요청 함수 섹션
# ==================================================

def fetch_soup(url):
    try:
        response = requests.get(
            url,
            headers=REQUEST_HEADERS,
            timeout=30
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        time.sleep(REQUEST_DELAY)

        print("=" * 50)
        print("URL:", url)
        print("=" * 50)

        print(soup.title)

        text = soup.get_text("\n", strip=True)

        print(text[:5000])

        return soup

    except Exception as error:
        print("페이지 요청 실패:", url)
        print(error)

        return None

# ==================================================
# 9. 페이지 링크 수집 함수 섹션
# ==================================================

def collect_page_urls(start_url):
    soup = fetch_soup(start_url)

    if soup is None:
        return []

    urls = [start_url]

    for link in soup.find_all("a"):
        href = link.get("href", "")

        if not href:
            continue

        if href.startswith("/"):
            href = BASE_URL + href

        if start_url.rstrip("/") in href.rstrip("/"):
            if href not in urls:
                urls.append(href)

    return urls


# ==================================================
# 10. 단어 행 분석 함수 섹션
# ==================================================

def parse_vocab_row(cells, cache):
    if len(cells) < 3:
        return None

    vocab_text = clean_text(cells[1].get_text(" "))
    meaning_text = clean_text(cells[-1].get_text(" "))

    if not vocab_text or not meaning_text:
        return None

    parts = vocab_text.split()

    if len(parts) == 1:
        word = parts[0]
        hiragana = parts[0]
        romaji = japanese_to_romaji(word)

    elif len(parts) >= 2:
        word = parts[0]

        if parts[1].isascii():
            romaji = normalize_romaji_key(parts[1])
            hiragana = parts[2] if len(parts) >= 3 else word

        else:
            hiragana = parts[1]
            romaji = japanese_to_romaji(hiragana)

    else:
        return None

    meaning = translate_to_korean(
        meaning_text,
        cache
    )

    row = {
        "word": word,
        "hiragana": hiragana,
        "meaning": meaning,
        "romaji": romaji,
        "score": 50,
        "used": "false",
        "day": ""
    }

    return row


# ==================================================
# 11. 문법 행 분석 함수 섹션
# ==================================================

def parse_grammar_row(cells, cache):
    if len(cells) < 2:
        return None

    grammar_text = clean_text(cells[1].get_text(" "))
    meaning_text = clean_text(cells[-1].get_text(" "))

    if not grammar_text:
        return None

    if not meaning_text or grammar_text == meaning_text:
        if len(cells) >= 3:
            meaning_text = clean_text(cells[2].get_text(" "))

    grammar_text = remove_number_prefix(grammar_text)

    parts = grammar_text.split()

    if not parts:
        return None

    word = parts[0]

    hiragana = word

    romaji = japanese_to_romaji(word)

    if len(parts) >= 2:
        for part in parts:
            if part.isascii() and len(part) >= 2:
                romaji = normalize_romaji_key(part)
                break

    meaning = translate_to_korean(
        meaning_text,
        cache
    )

    row = {
        "word": word,
        "hiragana": hiragana,
        "meaning": meaning,
        "romaji": romaji,
        "score": 50,
        "used": "false",
        "day": ""
    }

    return row


# ==================================================
# 12. 테이블 데이터 수집 함수 섹션
# ==================================================

def scrape_table_rows(urls, row_parser, cache):
    rows = []

    for url in urls:
        print("크롤링 중:", url)

        soup = fetch_soup(url)

        if soup is None:
            continue

        table_rows = soup.select("tr")

        for table_row in table_rows:
            cells = table_row.find_all(["td", "th"])
            
            print("셀 개수:", len(cells))

            for i, cell in enumerate(cells):
                print(i, cell.get_text(strip=True))

            break
            

            parsed_row = row_parser(
                cells,
                cache
            )

            if parsed_row:
                rows.append(parsed_row)

    return rows


# ==================================================
# 13. 레벨별 단어 크롤링 함수 섹션
# ==================================================

def scrape_vocab_for_level(level, cache):
    level_lower = level.lower()

    start_url = f"{BASE_URL}/jlpt-{level_lower}-vocabulary-list/"

    urls = collect_page_urls(start_url)

    rows = scrape_table_rows(
        urls,
        parse_vocab_row,
        cache
    )

    rows = fix_duplicate_romaji(rows)

    print(level, "단어 수집 완료:", len(rows), "개")

    return rows


# ==================================================
# 14. 레벨별 문법 크롤링 함수 섹션
# ==================================================

def scrape_grammar_for_level(level, cache):
    level_lower = level.lower()

    start_url = f"{BASE_URL}/jlpt-{level_lower}-grammar-list/"

    urls = collect_page_urls(start_url)

    rows = scrape_table_rows(
        urls,
        parse_grammar_row,
        cache
    )

    rows = fix_duplicate_romaji(rows)

    print(level, "문법 수집 완료:", len(rows), "개")

    return rows


# ==================================================
# 15. 프로젝트용 CSV 저장 함수 섹션
# ==================================================

def save_project_csv(level, data_type, rows):
    save_path = os.path.join(
        DATA_FOLDER,
        f"jlpt_{level.lower()}_{data_type}.csv"
    )

    with open(save_path, "w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=CSV_FIELDNAMES
        )

        writer.writeheader()

        for row in rows:
            writer.writerow(row)

    print(level, data_type, "CSV 저장 완료:", save_path)


# ==================================================
# 16. 전체 레벨 크롤링 함수 섹션
# ==================================================

def scrape_all_levels():
    ensure_data_folder()

    cache = load_translation_cache()

    for level in JLPT_LEVELS:
        print("===================================")
        print(level, "단어 크롤링 시작")
        print("===================================")

        vocab_rows = scrape_vocab_for_level(
            level,
            cache
        )

        save_project_csv(
            level,
            "vocab",
            vocab_rows
        )

        save_translation_cache(cache)

        print("===================================")
        print(level, "문법 크롤링 시작")
        print("===================================")

        grammar_rows = scrape_grammar_for_level(
            level,
            cache
        )

        save_project_csv(
            level,
            "grammar",
            grammar_rows
        )

        save_translation_cache(cache)

    print("전체 JLPT 단어/문법 크롤링 완료")


# ==================================================
# 17. 테스트 실행 섹션
# ==================================================

if __name__ == "__main__":
    ensure_data_folder()

    cache = load_translation_cache()

    rows = scrape_vocab_for_level(
        "N5",
        cache
    )

    print(rows[:5])