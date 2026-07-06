from pathlib import Path


DAY_VIDEO_ROOT = Path("output/day_videos")
THUMBNAIL_ROOT = Path("output/thumbnails")


def _normalize_level(level):
    return str(level).strip().upper()


def _day_text(day):
    return str(day).zfill(3)


def build_day_video_path(level, day, day_video_root=DAY_VIDEO_ROOT):
    level_text = _normalize_level(level)
    day = _day_text(day)
    return Path(day_video_root) / level_text / f"{level_text}_DAY_{day}.mp4"


def build_day_thumbnail_path(level, day, thumbnail_root=THUMBNAIL_ROOT):
    level_text = _normalize_level(level)
    day = _day_text(day)
    return Path(thumbnail_root) / f"{level_text}_DAY_{day}.jpg"


def _has_drive_backup(entry):
    if not isinstance(entry, dict):
        return False

    return bool(
        entry.get("drive_backed_up")
        and entry.get("drive_video_file_id")
    )


def build_compilation_source_status(
    levels,
    start_day,
    end_day,
    day_video_root=DAY_VIDEO_ROOT,
    thumbnail_root=THUMBNAIL_ROOT,
    log_data=None,
):
    log_data = log_data or {}
    rows = []

    for level in levels:
        level_text = _normalize_level(level)
        for day_number in range(int(start_day), int(end_day) + 1):
            day = _day_text(day_number)
            video_path = build_day_video_path(level_text, day, day_video_root=day_video_root)
            thumbnail_path = build_day_thumbnail_path(level_text, day, thumbnail_root=thumbnail_root)
            upload_key = f"{level_text}_DAY_{day}"
            drive_available = _has_drive_backup(log_data.get(upload_key))
            video_exists = video_path.exists()
            thumbnail_exists = thumbnail_path.exists()

            if video_exists:
                status = "ready"
            elif drive_available:
                status = "restorable"
            else:
                status = "missing"

            rows.append({
                "level": level_text,
                "day": day,
                "video_exists": video_exists,
                "thumbnail_exists": thumbnail_exists,
                "drive_available": drive_available,
                "can_restore": (not video_exists) and drive_available,
                "status": status,
                "video_path": str(video_path),
            })

    return rows


def ensure_compilation_sources(
    levels,
    start_day,
    end_day,
    restore_day,
    day_video_root=DAY_VIDEO_ROOT,
    thumbnail_root=THUMBNAIL_ROOT,
    log_data=None,
):
    rows = build_compilation_source_status(
        levels,
        start_day,
        end_day,
        day_video_root=day_video_root,
        thumbnail_root=thumbnail_root,
        log_data=log_data,
    )

    missing_rows = [row for row in rows if row["status"] == "missing"]
    if missing_rows:
        missing_text = ", ".join(
            f"{row['level']} DAY {row['day']}" for row in missing_rows
        )
        raise ValueError(f"풀영상 소스 영상이 없고 Drive 백업도 없습니다: {missing_text}")

    restore_results = []
    for row in rows:
        if not row["can_restore"]:
            continue

        print(f"{row['level']} DAY {row['day']} 소스 영상을 Google Drive에서 복원합니다.")
        restore_results.append(
            restore_day(row["level"], row["day"], overwrite=False)
        )

    return {
        "ready": True,
        "rows": rows,
        "restored": restore_results,
        "restored_count": len(restore_results),
        "missing_count": len(missing_rows),
    }
