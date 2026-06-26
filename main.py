# ==================================================
# File: main.py
# Role: run the full shorts pipeline for JLPT and business Japanese
# ==================================================

import asyncio
import os

from dotenv import load_dotenv

from src.cleanup.asset_cleanup import build_asset_manifest_from_current_words
from src.cleanup.asset_cleanup import cleanup_generated_assets_for_day
from src.data.business_word_provider import add_daily_business_items
from src.data.day_manager import get_current_day_number, increase_day_number
from src.drive.google_drive_uploader import backup_day_assets
from src.data.jlpt_word_provider import add_daily_items
from src.data.meaning_cleaner import clean_all
from src.image.image_generator import generate_images
from src.image.thumbnail_generator import generate_thumbnail
from src.tts.tts_generator import generate_tts_from_words
from src.video.day_video_generator import create_day_video
from src.video.video_batch_generator import generate_all_videos
from src.youtube.upload_log import get_upload_entry
from src.youtube.upload_log import update_uploaded_entry
from src.youtube.youtube_uploader import upload_by_level_day

JLPT_LEVELS = ["N1", "N2", "N3", "N4", "N5"]
BUSINESS_LEVELS = ["BUSINESS"]
# LEVELS = JLPT_LEVELS + BUSINESS_LEVELS
# LEVELS = BUSINESS_LEVELS
LEVELS = JLPT_LEVELS

AUTO_UPLOAD = True
COMPILATION_UNIT = 25
DAY_VIDEO_FOLDER = "output/day_videos"

load_dotenv()
UPLOAD_PUBLISH_AT = os.getenv("UPLOAD_PUBLISH_AT")


def get_compilation_range(day, unit=COMPILATION_UNIT):
    start_day = ((day - 1) // unit) * unit + 1
    end_day = start_day + unit - 1
    return start_day, end_day


def has_all_day_videos(level, start_day, end_day):
    for day in range(start_day, end_day + 1):
        day_text = str(day).zfill(3)
        video_path = os.path.join(
            DAY_VIDEO_FOLDER,
            level,
            f"{level}_DAY_{day_text}.mp4",
        )

        if not os.path.exists(video_path):
            print("Missing compilation source file:", video_path)
            return False

    return True


def prepare_daily_items(level):
    if level in JLPT_LEVELS:
        print("Prep: cleaning JLPT CSV meaning fields.")
        clean_all()
        print("Prep done: JLPT CSV meaning cleanup complete.")

        print("Step 0: add today's JLPT word/grammar items from CSV.")
        add_daily_items(level)
        print("Step 0 done: JLPT content added.")
        return

    print("Step 0: add today's business Japanese items from CSV.")
    add_daily_business_items(level)
    print("Step 0 done: business content added.")


def generate_pipeline(level):
    print(level, "start")

    day = get_current_day_number(level)
    day_text = str(day).zfill(3)

    print(level, "current day:", day_text)

    prepare_daily_items(level)

    print("Step 1: generate card images.")
    generate_images()
    print("Step 1 done: images generated.")

    print("Step 2: generate TTS audio.")
    asyncio.run(generate_tts_from_words())
    print("Step 2 done: TTS generated.")

    print("Step 3: generate shorts videos.")
    generate_all_videos()
    print("Step 3 done: shorts videos generated.")

    print("Step 4: generate the combined day video.")
    create_day_video(level)
    print("Step 4 done: day video generated.")

    print("Step 5: generate thumbnail.")
    generate_thumbnail(level=level, day=day_text)
    print("Step 5 done: thumbnail generated.")

    update_uploaded_entry(
        f"{str(level).strip().upper()}_DAY_{day_text}",
        generated=True,
        level=str(level).strip().upper(),
        day=day_text,
        asset_manifest=build_asset_manifest_from_current_words(),
    )

    increase_day_number(level)
    print(level, "generation done")

    return day_text


def get_latest_generated_day(level):
    latest_day = max(get_current_day_number(level) - 1, 1)
    return str(latest_day).zfill(3)


def upload_existing_day(level, day=None, privacy_status="private", publish_at=None):
    day_text = str(day).zfill(3) if day is not None else get_latest_generated_day(level)

    print("Step 6: upload to YouTube.")
    upload_by_level_day(
        level=level,
        day=day_text,
        privacy_status=privacy_status,
        publish_at=publish_at if publish_at is not None else (UPLOAD_PUBLISH_AT or None),
    )
    print("Step 6 done: YouTube upload complete.")

    return day_text


def backup_existing_day_to_drive(level, day=None, delete_local=False):
    day_text = str(day).zfill(3) if day is not None else get_latest_generated_day(level)

    print("Step 7: backup day assets to Google Drive.")
    result = backup_day_assets(level=level, day=day_text, delete_local=delete_local)
    print("Step 7 done: Google Drive backup complete.")

    if delete_local:
        print("Step 8 done: local files deleted after backup.")

    return result


def finalize_uploaded_day(level, day=None, delete_local=True, cleanup_intermediate=True):
    day_text = str(day).zfill(3) if day is not None else get_latest_generated_day(level)

    backup_result = backup_existing_day_to_drive(
        level=level,
        day=day_text,
        delete_local=delete_local,
    )

    cleanup_result = None
    if cleanup_intermediate:
        entry = get_upload_entry(f"{str(level).strip().upper()}_DAY_{day_text}")
        if entry and entry.get("uploaded"):
            cleanup_result = cleanup_generated_assets_for_day(level=level, day=day_text)

    return {
        "day": day_text,
        "backup": backup_result,
        "cleanup": cleanup_result,
    }


def run_pipeline(level, privacy_status="private", publish_at=None):
    day_text = generate_pipeline(level)

    if AUTO_UPLOAD:
        upload_existing_day(level, day_text, privacy_status=privacy_status, publish_at=publish_at)
        finalize_uploaded_day(level, day_text, delete_local=True, cleanup_intermediate=True)

    print(level, "done")


if __name__ == "__main__":
    print("main.py start")

    for level in LEVELS:
        print("processing level:", level)
        run_pipeline(level)

    print("main.py end")
