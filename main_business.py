import asyncio
import os

from dotenv import load_dotenv

from src.data.business_word_provider import add_daily_business_items
from src.data.day_manager import get_current_day_number, increase_day_number
from src.image.image_generator import generate_images
from src.image.thumbnail_generator import generate_thumbnail
from src.tts.tts_generator import generate_tts_from_words
from src.video.day_video_generator import create_day_video
from src.video.video_batch_generator import generate_all_videos
from src.youtube.youtube_uploader import upload_by_level_day

BUSINESS_LEVEL = "BUSINESS"
AUTO_UPLOAD = True

load_dotenv()
UPLOAD_PUBLISH_AT = os.getenv("UPLOAD_PUBLISH_AT")


def run_business_pipeline():
    print(BUSINESS_LEVEL, "start")

    day = get_current_day_number(BUSINESS_LEVEL)
    day_text = str(day).zfill(3)

    print(BUSINESS_LEVEL, "current day:", day_text)

    print("Step 0: load today's business Japanese items from CSV.")
    add_daily_business_items(BUSINESS_LEVEL)

    print("Step 1: generate card images.")
    generate_images()

    print("Step 2: generate TTS audio.")
    asyncio.run(generate_tts_from_words())

    print("Step 3: generate shorts videos.")
    generate_all_videos()

    print("Step 4: generate the combined day video.")
    create_day_video(BUSINESS_LEVEL)

    print("Step 5: generate thumbnail.")
    generate_thumbnail(level=BUSINESS_LEVEL, day=day_text)

    if AUTO_UPLOAD:
        print("Step 6: upload to YouTube.")
        upload_by_level_day(
            level=BUSINESS_LEVEL,
            day=day_text,
            privacy_status="private",
            publish_at=UPLOAD_PUBLISH_AT or None,
        )

    increase_day_number(BUSINESS_LEVEL)
    print(BUSINESS_LEVEL, "done")


if __name__ == "__main__":
    print("main_business.py start")
    run_business_pipeline()
    print("main_business.py end")
