# ==================================================
# 파일명: level_thumbnail_generator.py
# 역할: 레벨별 묶음 영상용 썸네일 생성 모듈
# 예시: N1 DAY001~025 전체 영상용 썸네일
# ==================================================

import os

from PIL import Image, ImageDraw, ImageFont


# ==================================================
# 1. 기본 설정
# ==================================================

THUMBNAIL_SIZE = (1280, 720)

BACKGROUND_MAP = {
    "N1": "assets/backgrounds/n1.png",
    "N2": "assets/backgrounds/n2.png",
    "N3": "assets/backgrounds/n3.png",
    "N4": "assets/backgrounds/n4.png",
    "N5": "assets/backgrounds/n5.png",
}

OUTPUT_FOLDER = "output/thumbnails/level"

FONT_PATH = "assets/fonts/GodoB.otf"


# ==================================================
# 2. 폴더 생성
# ==================================================

def ensure_output_folder():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)


# ==================================================
# 3. 폰트 불러오기
# ==================================================

def load_font(size):
    return ImageFont.truetype(FONT_PATH, size)


# ==================================================
# 4. 가운데 텍스트 그리기
# ==================================================

def draw_center_text(
    draw,
    text,
    y,
    font,
    fill="white",
    stroke_width=4
):
    bbox = draw.textbbox(
        (0, 0),
        text,
        font=font,
        stroke_width=stroke_width
    )

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


# ==================================================
# 5. 묶음 영상용 썸네일 생성
# ==================================================

def generate_level_thumbnail(
    level="N1",
    start_day=1,
    end_day=25
):
    ensure_output_folder()

    start_day_text = str(start_day).zfill(3)
    end_day_text = str(end_day).zfill(3)

    background_path = BACKGROUND_MAP.get(level)

    if not background_path:
        print("지원하지 않는 레벨입니다:", level)
        return ""

    if not os.path.exists(background_path):
        print("배경 이미지를 찾을 수 없습니다:", background_path)
        return ""

    image = Image.open(background_path).convert("RGB")
    image = image.resize(THUMBNAIL_SIZE)

    draw = ImageDraw.Draw(image)

    title_font = load_font(80)
    subtitle_font = load_font(58)
    range_font = load_font(95)

    draw_center_text(
        draw,
        f"JLPT {level}",
        115,
        title_font,
        fill="white",
        stroke_width=5
    )

    draw_center_text(
        draw,
        "일본어 단어 + 문법",
        245,
        subtitle_font,
        fill="white",
        stroke_width=5
    )

    draw_center_text(
        draw,
        f"DAY {start_day_text} ~ {end_day_text}",
        390,
        range_font,
        fill="white",
        stroke_width=7
    )

    output_path = os.path.join(
        OUTPUT_FOLDER,
        f"{level}_DAY_{start_day_text}_{end_day_text}_FULL.jpg"
    )

    image.save(
        output_path,
        quality=95
    )

    print("묶음 영상 썸네일 생성 완료:", output_path)

    return output_path


# ==================================================
# 6. 테스트 실행
# ==================================================

if __name__ == "__main__":
    generate_level_thumbnail(
        level="N1",
        start_day=1,
        end_day=25
    )