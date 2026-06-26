from PIL import Image, ImageDraw, ImageFont

import json
import os
import textwrap

from src.utils.filename_utils import normalize_romaji_filename

image_folder = "assets/images"
words_file = "data/words.json"
font_folder = "assets/fonts"
background_folder = "assets/backgrounds"

japanese_font_path = os.path.join(font_folder, "NotoSansJP-Bold.ttf")
korean_font_path = os.path.join(font_folder, "NotoSansKR-Bold.ttf")

DEFAULT_BACKGROUND_PATH = os.path.join(background_folder, "default.jpg")
BUSINESS_BACKGROUND_PATH = os.path.join(background_folder, "business_office.jpg")

os.makedirs(image_folder, exist_ok=True)
os.makedirs(background_folder, exist_ok=True)

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


def load_words():
    try:
        with open(words_file, "r", encoding="utf-8") as files:
            return json.load(files)
    except FileNotFoundError:
        print("words.json file not found.")
        return []
    except json.JSONDecodeError:
        print("words.json is invalid.")
        return []


def load_font(font_path, font_size):
    try:
        return ImageFont.truetype(font_path, font_size)
    except Exception:
        print("Font file not found. Using default font.")
        return ImageFont.load_default()


def get_center_position(draw, text, font, y):
    text_box = draw.textbbox((0, 0), text, font=font)
    text_width = text_box[2] - text_box[0]
    x = (WIDTH - text_width) // 2
    return (x, y)


def get_multiline_center_position(draw, text, font, y, line_spacing=20):
    lines = text.split("\n")
    max_width = 0
    total_height = 0

    for line in lines:
        text_box = draw.textbbox((0, 0), line, font=font)
        line_width = text_box[2] - text_box[0]
        line_height = text_box[3] - text_box[1]
        max_width = max(max_width, line_width)
        total_height += line_height + line_spacing

    total_height -= line_spacing
    x = (WIDTH - max_width) // 2
    return (x, y), total_height


def draw_text_with_shadow(draw, position, text, font, text_color, shadow_color, shadow_offset=4):
    x, y = position
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=shadow_color)
    draw.text((x, y), text, font=font, fill=text_color)


def draw_multiline_text_with_shadow(draw, position, text, font, text_color, shadow_color, shadow_offset=4, line_spacing=20):
    x, y = position
    lines = text.split("\n")
    current_y = y

    for line in lines:
        text_box = draw.textbbox((0, 0), line, font=font)
        line_width = text_box[2] - text_box[0]
        line_height = text_box[3] - text_box[1]
        line_x = (WIDTH - line_width) // 2
        draw.text((line_x + shadow_offset, current_y + shadow_offset), line, font=font, fill=shadow_color)
        draw.text((line_x, current_y), line, font=font, fill=text_color)
        current_y += line_height + line_spacing


def wrap_meaning_text(meaning, width=16):
    meaning = meaning.strip()
    meaning = meaning.replace(",", ", ")
    meaning = " ".join(meaning.split())
    return "\n".join(textwrap.wrap(meaning, width=width))


def create_background_image(background_path):
    if background_path and os.path.exists(background_path):
        background = Image.open(background_path).convert("RGB")
        background = background.resize((WIDTH, HEIGHT))
        overlay = Image.new("RGB", (WIDTH, HEIGHT), OVERLAY_COLOR)
        return Image.blend(background, overlay, OVERLAY_ALPHA)

    return Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND_COLOR)


def get_content_labels(level, item_type):
    level = str(level).strip().upper()
    item_type = str(item_type).strip().lower()

    if level == "BUSINESS":
        return "BUSINESS JAPANESE"

    if item_type == "grammar":
        return f"JLPT {level} GRAMMAR"

    return f"JLPT {level} WORD"


def get_background_path(level):
    level = str(level).strip().upper()

    if level == "BUSINESS" and os.path.exists(BUSINESS_BACKGROUND_PATH):
        return BUSINESS_BACKGROUND_PATH

    return DEFAULT_BACKGROUND_PATH


def load_auto_fit_font(draw, text, font_path, start_size, min_size, max_width):
    font_size = start_size

    while font_size >= min_size:
        font = load_font(font_path, font_size)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]

        if text_width <= max_width:
            return font

        font_size -= 5

    return load_font(font_path, min_size)


def create_word_image(current_word):
    word = current_word.get("word", "")
    hiragana = current_word.get("hiragana", "")
    meaning = current_word.get("meaning", "")
    romaji = current_word.get("romaji", "")
    item_type = current_word.get("type", "vocab")
    day_text = current_word.get("day_text", "")

    if not romaji:
        print("Missing romaji; skipping image generation.")
        return

    if not word or not hiragana or not meaning:
        print("Missing required word fields; skipping image generation.")
        return

    level = current_word.get("level", "N1")
    top_label = get_content_labels(level, item_type)
    wrapped_meaning = wrap_meaning_text(meaning, width=16)

    image = create_background_image(get_background_path(level))
    draw = ImageDraw.Draw(image)

    if item_type in {"grammar", "business_phrase"}:
        word_font = load_auto_fit_font(draw, word, japanese_font_path, 110, 55, 920)
        hiragana_font = load_auto_fit_font(draw, hiragana, japanese_font_path, 75, 45, 900)
        meaning_font = load_auto_fit_font(draw, wrapped_meaning, korean_font_path, 65, 42, 900)
    else:
        word_font = load_font(japanese_font_path, WORD_FONT_SIZE)
        hiragana_font = load_font(japanese_font_path, HIRAGANA_FONT_SIZE)
        meaning_font = load_font(korean_font_path, MEANING_FONT_SIZE)

    level_font = load_font(japanese_font_path, LEVEL_FONT_SIZE)
    day_font = load_font(japanese_font_path, DAY_FONT_SIZE)

    word_position = get_center_position(draw, word, word_font, 610)
    hiragana_position = get_center_position(draw, hiragana, hiragana_font, 800)
    meaning_position, _ = get_multiline_center_position(draw, wrapped_meaning, meaning_font, 1000, line_spacing=22)
    level_position = get_center_position(draw, top_label, level_font, 120)
    day_position = get_center_position(draw, day_text, day_font, 180)

    draw_text_with_shadow(draw, level_position, top_label, level_font, TEXT_COLOR, SHADOW_COLOR)
    draw_text_with_shadow(draw, day_position, day_text, day_font, TEXT_COLOR, SHADOW_COLOR)
    draw_text_with_shadow(draw, word_position, word, word_font, TEXT_COLOR, SHADOW_COLOR)
    draw_text_with_shadow(draw, hiragana_position, hiragana, hiragana_font, TEXT_COLOR, SHADOW_COLOR)
    draw_multiline_text_with_shadow(draw, meaning_position, wrapped_meaning, meaning_font, MEANING_COLOR, SHADOW_COLOR, line_spacing=22)

    filename = normalize_romaji_filename(romaji) + ".png"
    save_path = os.path.join(image_folder, filename)
    image.save(save_path)
    print("Image generated:", save_path)


def generate_images():
    words = load_words()

    if not words:
        print("No words to process.")
        return

    for current_word in words:
        create_word_image(current_word)
