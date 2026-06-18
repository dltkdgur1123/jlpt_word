# ==================================================
# 파일명: image_generator.py
# 역할: 일본어 단어 학습용 쇼츠 이미지 생성 모듈
# ==================================================


# ==================================================
# 1. 라이브러리 import 섹션
# ==================================================

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import os
import json
import textwrap


# ==================================================
# 2. 기본 경로 설정 섹션
# ==================================================

image_folder = "assets/images"
words_file = "data/words.json"
font_folder = "assets/fonts"
background_folder = "assets/backgrounds"

japanese_font_path = os.path.join(font_folder, "NotoSansJP-Bold.ttf")
korean_font_path = os.path.join(font_folder, "NotoSansKR-Bold.ttf")

if not os.path.exists(image_folder):
    os.makedirs(image_folder)

if not os.path.exists(background_folder):
    os.makedirs(background_folder)


# ==================================================
# 3. 이미지 기본 설정 섹션
# ==================================================

WIDTH = 1080
HEIGHT = 1920

BACKGROUND_COLOR = (245, 242, 235)
OVERLAY_COLOR = (255, 255, 255)
OVERLAY_ALPHA = 0.5

TEXT_COLOR = (255, 255, 255)
MEANING_COLOR = (255, 255, 255)
SHADOW_COLOR = (0, 0, 0)

WORD_FONT_SIZE = 150
HIRAGANA_FONT_SIZE = 90
MEANING_FONT_SIZE = 80

LEVEL_FONT_SIZE = 45
DAY_FONT_SIZE = 40


# ==================================================
# 4. 단어 데이터 불러오기 함수 섹션
# ==================================================

def load_words():
    try:
        with open(words_file, "r", encoding="utf-8") as files:
            words = json.load(files)
            return words

    except FileNotFoundError:
        print("words.json 파일을 찾을 수 없습니다.")
        return []

    except json.JSONDecodeError:
        print("words.json 형식이 올바르지 않습니다.")
        return []


# ==================================================
# 5. 폰트 불러오기 함수 섹션
# ==================================================

def load_font(font_path, font_size):
    try:
        font = ImageFont.truetype(font_path, font_size)
        return font

    except:
        print("폰트 파일을 찾을 수 없어 기본 폰트를 사용합니다.")
        font = ImageFont.load_default()
        return font


# ==================================================
# 6. 텍스트 중앙 위치 계산 함수 섹션
# ==================================================

def get_center_position(draw, text, font, y):
    text_box = draw.textbbox(
        (0, 0),
        text,
        font=font
    )

    text_width = text_box[2] - text_box[0]

    x = (WIDTH - text_width) // 2

    return (x, y)


def get_multiline_center_position(draw, text, font, y, line_spacing=20):
    lines = text.split("\n")

    max_width = 0
    total_height = 0

    for line in lines:
        text_box = draw.textbbox(
            (0, 0),
            line,
            font=font
        )

        line_width = text_box[2] - text_box[0]
        line_height = text_box[3] - text_box[1]

        if line_width > max_width:
            max_width = line_width

        total_height = total_height + line_height + line_spacing

    total_height = total_height - line_spacing

    x = (WIDTH - max_width) // 2

    return (x, y), total_height


def draw_text_with_shadow(
    draw,
    position,
    text,
    font,
    text_color,
    shadow_color,
    shadow_offset=4
):
    x, y = position

    draw.text(
        (x + shadow_offset, y + shadow_offset),
        text,
        font=font,
        fill=shadow_color
    )

    draw.text(
        (x, y),
        text,
        font=font,
        fill=text_color
    )


def draw_multiline_text_with_shadow(
    draw,
    position,
    text,
    font,
    text_color,
    shadow_color,
    shadow_offset=4,
    line_spacing=20
):
    x, y = position

    lines = text.split("\n")
    current_y = y

    for line in lines:
        text_box = draw.textbbox(
            (0, 0),
            line,
            font=font
        )

        line_width = text_box[2] - text_box[0]
        line_height = text_box[3] - text_box[1]

        line_x = (WIDTH - line_width) // 2

        draw.text(
            (line_x + shadow_offset, current_y + shadow_offset),
            line,
            font=font,
            fill=shadow_color
        )

        draw.text(
            (line_x, current_y),
            line,
            font=font,
            fill=text_color
        )

        current_y = current_y + line_height + line_spacing


# ==================================================
# 7. 한국어 뜻 자동 줄바꿈 함수 섹션
# ==================================================

def wrap_meaning_text(meaning, width=16):
    meaning = meaning.strip()

    meaning = meaning.replace(",", ", ")
    meaning = " ".join(meaning.split())

    wrapped_text = "\n".join(
        textwrap.wrap(
            meaning,
            width=width
        )
    )

    return wrapped_text


# ==================================================
# 8. 배경 이미지 생성 함수 섹션
# ==================================================

def create_background_image(background_path):
    if background_path and os.path.exists(background_path):
        background = Image.open(background_path).convert("RGB")
        background = background.resize((WIDTH, HEIGHT))

        overlay = Image.new("RGB", (WIDTH, HEIGHT), OVERLAY_COLOR)

        image = Image.blend(background, overlay, OVERLAY_ALPHA)

        return image

    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND_COLOR)

    return image


# ==================================================
# 9. 단어 이미지 생성 함수 섹션
# ==================================================

def create_word_image(current_word):
    word = current_word.get("word", "")
    hiragana = current_word.get("hiragana", "")
    meaning = current_word.get("meaning", "")
    romaji = current_word.get("romaji", "")
    item_type = current_word.get("type", "vocab")
    day_text = current_word.get("day_text", "")

    if not romaji:
        print("romaji 값이 없어서 이미지 생성을 건너뜁니다.")
        return

    if not word or not hiragana or not meaning:
        print("필수 단어 데이터가 부족해서 이미지 생성을 건너뜁니다.")
        return

    background_path = "assets/backgrounds/default.jpg"

    image = create_background_image(background_path)

    draw = ImageDraw.Draw(image)

    level = current_word.get("level", "N1")

    wrapped_meaning = wrap_meaning_text(
        meaning,
        width=16
    )

    if item_type == "grammar":
        jlpt_level = f"JLPT {level} GRAMMAR"

        word_font = load_auto_fit_font(
            draw,
            word,
            japanese_font_path,
            110,
            55,
            920
        )

        hiragana_font = load_auto_fit_font(
            draw,
            hiragana,
            japanese_font_path,
            75,
            45,
            900
        )

        meaning_font = load_auto_fit_font(
            draw,
            wrapped_meaning,
            korean_font_path,
            65,
            42,
            900
        )

    else:
        jlpt_level = f"JLPT {level} WORD"

        word_font = load_font(japanese_font_path, WORD_FONT_SIZE)
        hiragana_font = load_font(japanese_font_path, HIRAGANA_FONT_SIZE)
        meaning_font = load_font(korean_font_path, MEANING_FONT_SIZE)

    level_font = load_font(japanese_font_path, LEVEL_FONT_SIZE)
    day_font = load_font(japanese_font_path, DAY_FONT_SIZE)

    word_position = get_center_position(draw, word, word_font, 610)
    hiragana_position = get_center_position(draw, hiragana, hiragana_font, 800)

    meaning_position, meaning_total_height = get_multiline_center_position(
        draw,
        wrapped_meaning,
        meaning_font,
        1000,
        line_spacing=22
    )

    level_position = get_center_position(draw, jlpt_level, level_font, 120)
    day_position = get_center_position(draw, day_text, day_font, 180)

    draw_text_with_shadow(
        draw,
        level_position,
        jlpt_level,
        level_font,
        TEXT_COLOR,
        SHADOW_COLOR
    )

    draw_text_with_shadow(
        draw,
        day_position,
        day_text,
        day_font,
        TEXT_COLOR,
        SHADOW_COLOR
    )

    draw_text_with_shadow(
        draw,
        word_position,
        word,
        word_font,
        TEXT_COLOR,
        SHADOW_COLOR
    )

    draw_text_with_shadow(
        draw,
        hiragana_position,
        hiragana,
        hiragana_font,
        TEXT_COLOR,
        SHADOW_COLOR
    )

    draw_multiline_text_with_shadow(
        draw,
        meaning_position,
        wrapped_meaning,
        meaning_font,
        MEANING_COLOR,
        SHADOW_COLOR,
        line_spacing=22
    )

    filename = romaji.strip().replace(" ", "_") + ".png"

    save_path = os.path.join(
        image_folder,
        filename
    )

    image.save(save_path)

    print("이미지 생성 완료:", save_path)


# ==================================================
# 10. 폰트 자동 축소
# ==================================================

def load_auto_fit_font(draw, text, font_path, start_size, min_size, max_width):
    font_size = start_size

    while font_size >= min_size:
        font = load_font(font_path, font_size)

        bbox = draw.textbbox(
            (0, 0),
            text,
            font=font
        )

        text_width = bbox[2] - bbox[0]

        if text_width <= max_width:
            return font

        font_size = font_size - 5

    return load_font(font_path, min_size)


# ==================================================
# 11. 전체 이미지 생성 함수 섹션
# ==================================================

def generate_images():
    words = load_words()

    if not words:
        print("처리할 단어 데이터가 없습니다.")
        return

    for current_word in words:
        create_word_image(current_word)


# ==================================================
# 12. 직접 실행 섹션
# ==================================================

if __name__ == "__main__":
    generate_images()