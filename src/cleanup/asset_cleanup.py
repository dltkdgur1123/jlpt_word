import json
import os
from pathlib import Path

from src.utils.filename_utils import normalize_romaji_filename
from src.youtube.upload_log import get_upload_entry, update_uploaded_entry


WORDS_FILE = Path("data/words.json")
IMAGE_ROOT = Path("assets/images")
AUDIO_ROOT = Path("assets/audio")
WORD_VIDEO_ROOT = Path("output/videos")


def load_current_words():
    if not WORDS_FILE.exists():
        return []

    with WORDS_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def build_asset_manifest_from_current_words():
    words = load_current_words()
    manifest = []

    for item in words:
        romaji = str(item.get("romaji", "")).strip()
        if not romaji:
            continue

        safe_romaji = normalize_romaji_filename(romaji)
        manifest.append({
            "romaji": romaji,
            "safe_romaji": safe_romaji,
            "image": str(IMAGE_ROOT / f"{safe_romaji}.png"),
            "jp_audio": str(AUDIO_ROOT / f"{safe_romaji}_jp.mp3"),
            "kr_audio": str(AUDIO_ROOT / f"{safe_romaji}_kr.mp3"),
            "word_video": str(WORD_VIDEO_ROOT / f"{safe_romaji}.mp4"),
        })

    return manifest


def delete_file_if_exists(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False


def cleanup_generated_assets_for_day(level, day):
    upload_key = f"{str(level).strip().upper()}_DAY_{str(day).zfill(3)}"
    entry = get_upload_entry(upload_key)

    if not entry:
        return {
            "upload_key": upload_key,
            "deleted_files": [],
            "skipped": True,
            "reason": "업로드 로그 항목이 없습니다.",
        }

    asset_manifest = entry.get("asset_manifest") or []
    if not asset_manifest:
        return {
            "upload_key": upload_key,
            "deleted_files": [],
            "skipped": True,
            "reason": "정리할 중간 산출물 목록이 기록되어 있지 않습니다.",
        }

    deleted_files = []
    for item in asset_manifest:
        for field in ("image", "jp_audio", "kr_audio", "word_video"):
            file_path = item.get(field)
            if file_path and delete_file_if_exists(file_path):
                deleted_files.append(file_path)

    update_uploaded_entry(
        upload_key,
        asset_cleanup_done=True,
        cleaned_asset_count=len(deleted_files),
    )

    return {
        "upload_key": upload_key,
        "deleted_files": deleted_files,
        "skipped": False,
        "reason": "",
    }
