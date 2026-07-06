from pathlib import Path


DAY_VIDEO_ROOT = Path("output/day_videos")
THUMBNAIL_ROOT = Path("output/thumbnails")


def classify_generation_day(level, requested_day, next_day):
    level_text = str(level).strip().upper()
    day_number = int(requested_day)
    next_day_number = int(next_day)

    if day_number < 1:
        raise ValueError("DAY는 1 이상이어야 합니다.")

    return {
        "level": level_text,
        "day": day_number,
        "day_text": f"{day_number:03d}",
        "next_day": next_day_number,
        "execution_mode": "regenerate" if day_number < next_day_number else "generate",
        "is_historical": day_number < next_day_number,
    }


def build_regeneration_preview(
    level,
    day,
    day_video_root=DAY_VIDEO_ROOT,
    thumbnail_root=THUMBNAIL_ROOT,
):
    level_text = str(level).strip().upper()
    day_text = str(int(day)).zfill(3)
    video_path = Path(day_video_root) / level_text / f"{level_text}_DAY_{day_text}.mp4"
    thumbnail_path = Path(thumbnail_root) / f"{level_text}_DAY_{day_text}.jpg"

    return {
        "level": level_text,
        "day": day_text,
        "video_exists": video_path.exists(),
        "thumbnail_exists": thumbnail_path.exists(),
        "video_path": str(video_path),
        "thumbnail_path": str(thumbnail_path),
    }
