import os
from PIL import Image, ImageDraw, ImageFont

THUMBNAIL_SIZE = (1280, 720)

BACKGROUND_MAP = {
    "N1": "assets/backgrounds/n1.png",
    "N2": "assets/backgrounds/n2.png",
    "N3": "assets/backgrounds/n3.png",
    "N4": "assets/backgrounds/n4.png",
    "N5": "assets/backgrounds/n5.png",
}

OUTPUT_FOLDER = "output/thumbnails"

FONT_PATH = "assets/fonts/GodoB.otf"


def ensure_output_folder():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)


def load_font(size):
    return ImageFont.truetype(FONT_PATH, size)


def draw_center_text(draw, text, y, font, fill="white", stroke_width=4):
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
    text_width = bbox[2] - bbox[0]

    x = (THUMBNAIL_SIZE[0] - text_width) / 2

    draw.text(
        (x, y),
        text,
        font=font,
        fill=fill,
        stroke_width=stroke_width,
        stroke_fill="black"
    )


def generate_thumbnail(level="N1", day="001"):
    ensure_output_folder()

    background_path = BACKGROUND_MAP[level]

    image = Image.open(background_path).convert("RGB")
    image = image.resize(THUMBNAIL_SIZE)

    draw = ImageDraw.Draw(image)

    title_font = load_font(80)
    day_font = load_font(150)


    draw_center_text(
        draw,
        f"JLPT {level}",
        105,
        title_font,
        fill="white",
        stroke_width=5
    )

    draw_center_text(
        draw,
        f"DAY {day}",
        275,
        day_font,
        fill="white",
        stroke_width=7
    )


    output_path = os.path.join(
        OUTPUT_FOLDER,
        f"{level}_DAY_{day}.jpg"
    )

    image.save(output_path, quality=95)

    print("썸네일 생성 완료:", output_path)


if __name__ == "__main__":
    generate_thumbnail("N1", "001")