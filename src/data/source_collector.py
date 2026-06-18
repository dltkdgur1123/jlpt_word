# ==================================================
# 파일명: source_collector.py
# 역할: 외부 참고 사이트에서 JLPT 단어/문법 등장 자료를 수집해 source_data.csv로 저장하는 도구
# ==================================================


# ==================================================
# 1. 라이브러리 import 섹션
# ==================================================

import csv
import os
import re
import time

import requests
from bs4 import BeautifulSoup


# ==================================================
# 2. 기본 설정 섹션
# ==================================================

DATA_FOLDER = "data"

OUTPUT_FILE = os.path.join(
    DATA_FOLDER,
    "source_data.csv"
)

CSV_FIELDNAMES = [
    "item",
    "type",
    "level",
    "source",
    "url"
]

SOURCE_NAME = "japanesetest4you"

BASE_URL = "https://japanesetest4you.com"

HEADERS = {
    "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 "
    "(KHTML, like Gecko) "
    "Chrome/137.0.0.0 Safari/537.36",

    "Accept":
    "text/html,application/xhtml+xml,"
    "application/xml;q=0.9,image/avif,"
    "image/webp,*/*;q=0.8",

    "Accept-Language":
    "en-US,en;q=0.9",

    "Referer":
    "https://www.google.com/"
}

REQUEST_DELAY = 1.0

LEVELS = [
    "N1",
    "N2",
    "N3",
    "N4",
    "N5"
]


# ==================================================
# 3. 폴더 생성 섹션
# ==================================================

def ensure_data_folder():
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)


# ==================================================
# 4. 텍스트 정리 함수 섹션
# ==================================================

def clean_text(text):
    if not text:
        return ""

    text = text.replace("\n", " ")
    text = text.replace("\t", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def contains_japanese(text):
    if not text:
        return False

    for char in text:
        code = ord(char)

        if 0x3040 <= code <= 0x30FF:
            return True

        if 0x4E00 <= code <= 0x9FFF:
            return True

    return False


def normalize_item(text):
    text = clean_text(text)

    text = text.replace("~", "～")
    text = text.replace("〜", "～")

    text = text.strip("「」『』[]()（）:：,，.。 ")

    return text


# ==================================================
# 5. 페이지 요청 함수 섹션
# ==================================================

def fetch_soup(url):
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        time.sleep(REQUEST_DELAY)
        
        print("=" * 60)
        print("URL:", url)
        print("TITLE:", soup.title)

        text = soup.get_text("\n", strip=True)
        print(text[:2000])
        print("=" * 60)
        
        

        return soup

    except Exception as error:
        print("페이지 요청 실패:", url)
        print(error)

        return None


# ==================================================
# 6. source 행 생성 함수 섹션
# ==================================================

def create_source_row(item, item_type, level, url):
    return {
        "item": item,
        "type": item_type,
        "level": level,
        "source": SOURCE_NAME,
        "url": url
    }


# ==================================================
# 7. Japanesetest4you URL 생성 섹션
# ==================================================

def get_japanesetest4you_urls(level, item_type):
    level_lower = level.lower()

    if item_type == "vocab":
        return [
            f"{BASE_URL}/jlpt-{level_lower}-vocabulary-list/"
        ]

    if item_type == "grammar":
        return [
            f"{BASE_URL}/jlpt-{level_lower}-grammar-list/"
        ]

    return []


# ==================================================
# 8. 후보 텍스트 추출 함수 섹션
# ==================================================

def extract_candidate_items_from_soup(soup):
    items = []

    if soup is None:
        return items

    text = soup.get_text("\n", strip=True)

    lines = text.split("\n")

    for line in lines:
        line = clean_text(line)

        if not line:
            continue

        if not contains_japanese(line):
            continue

        # 예: たい (tai)
        match = re.match(
            r"^([一-龥ぁ-んァ-ンー～〜]+)\s*\([A-Za-z0-9_ -]+\)",
            line
        )

        if match:
            item = normalize_item(match.group(1))

            if item:
                items.append(item)

    print("items 개수:", len(items))

    return items


# ==================================================
# 9. 텍스트에서 단어/문법 후보 추출 함수 섹션
# ==================================================

# def extract_item_from_text(text):
#     text = clean_text(text)

#     if not text:
#         return ""

#     patterns = [
#         r"([一-龥ぁ-んァ-ンー]+)",
#         r"(～[一-龥ぁ-んァ-ンーA-Za-z0-9]+)",
#         r"(〜[一-龥ぁ-んァ-ンーA-Za-z0-9]+)"
#     ]

#     for pattern in patterns:
#         match = re.search(pattern, text)

#         if match:
#             item = normalize_item(match.group(1))

#             if len(item) == 0:
#                 return ""

#             return item

#     return ""


# ==================================================
# 10. 단일 URL 수집 함수 섹션
# ==================================================

def collect_from_url(level, item_type, url):
    print("수집 중:", level, item_type, url)

    soup = fetch_soup(url)

    if soup is None:
        return []

    candidates = extract_candidate_items_from_soup(soup)
    
    print("후보 샘플")

    for item in candidates[:20]:
        print(item)
    

    rows = []

    for candidate in candidates:
        row = create_source_row(
            candidate,
            item_type,
            level,
            url
        )

        rows.append(row)

    print("수집 후보 수:", len(rows))

    return rows


# ==================================================
# 11. 전체 수집 함수 섹션
# ==================================================

def collect_japanesetest4you_sources():
    all_rows = []

    for level in LEVELS:
        for item_type in ["vocab", "grammar"]:
            urls = get_japanesetest4you_urls(
                level,
                item_type
            )

            for url in urls:
                rows = collect_from_url(
                    level,
                    item_type,
                    url
                )

                all_rows.extend(rows)

    return all_rows


# ==================================================
# 12. 중복 제거 함수 섹션
# ==================================================

def remove_duplicate_rows(rows):
    seen = set()
    unique_rows = []

    for row in rows:
        key = (
            row.get("item", ""),
            row.get("type", ""),
            row.get("level", ""),
            row.get("source", "")
        )

        if key in seen:
            continue

        seen.add(key)
        unique_rows.append(row)

    return unique_rows


# ==================================================
# 13. CSV 저장 함수 섹션
# ==================================================

def save_source_data(rows):
    rows = remove_duplicate_rows(rows)

    with open(
        OUTPUT_FILE,
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

    print("source_data.csv 저장 완료:", OUTPUT_FILE)
    print("총 수집 수:", len(rows))


# ==================================================
# 14. 전체 실행 함수 섹션
# ==================================================

def collect_all_sources():
    ensure_data_folder()

    rows = collect_japanesetest4you_sources()

    save_source_data(rows)

    print("외부 source 수집 완료")


# ==================================================
# 15. 테스트 실행 섹션
# ==================================================

if __name__ == "__main__":
    collect_all_sources()