from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

AUTOMATION_LEVELS = ["N1", "N2", "N3", "N4", "N5", "BUSINESS"]
KST = ZoneInfo("Asia/Seoul")
UTC = ZoneInfo("UTC")


def evaluate_generation_readiness(level, remaining_counts):
    level_text = str(level).strip().upper()
    remaining_vocab = int(remaining_counts.get("remaining_vocab", 0) or 0)

    if level_text == "BUSINESS":
        remaining_secondary = int(remaining_counts.get("remaining_phrases", 0) or 0)
        required_vocab = 3
        required_secondary = 4
        secondary_label = "phrases"
    else:
        remaining_secondary = int(remaining_counts.get("remaining_grammar", 0) or 0)
        required_vocab = 5
        required_secondary = 2
        secondary_label = "grammar"

    if remaining_vocab < required_vocab:
        reason = "insufficient_vocab"
        ready = False
    elif remaining_secondary < required_secondary:
        reason = f"insufficient_{secondary_label}"
        ready = False
    else:
        reason = "ready"
        ready = True

    return {
        "level": level_text,
        "ready": ready,
        "reason": reason,
        "remaining_vocab": remaining_vocab,
        f"remaining_{secondary_label}": remaining_secondary,
        "required_vocab": required_vocab,
        f"required_{secondary_label}": required_secondary,
    }


def get_latest_reserved_publish_at(entries):
    latest = None
    for value in (entries or {}).values():
        if not isinstance(value, dict):
            continue
        if not value.get("uploaded"):
            continue
        publish_at = value.get("publish_at")
        if not publish_at:
            continue
        try:
            current = datetime.fromisoformat(str(publish_at).replace("Z", "+00:00"))
        except ValueError:
            continue
        if latest is None or current > latest:
            latest = current
    return latest.isoformat() if latest else None


def build_publish_schedule(count, latest_publish_at=None, now_kst=None, morning_hour=8, evening_hour=18):
    if count <= 0:
        return []

    now_value = now_kst or datetime.now(KST)
    if now_value.tzinfo is None:
        now_value = now_value.replace(tzinfo=KST)
    else:
        now_value = now_value.astimezone(KST)

    if latest_publish_at:
        latest = datetime.fromisoformat(str(latest_publish_at).replace("Z", "+00:00")).astimezone(KST)
        base_date = latest.date() + timedelta(days=1)
    else:
        base_date = now_value.date() + timedelta(days=1)

    slots = []
    day_offset = 0
    for index in range(count):
        publish_date = base_date + timedelta(days=day_offset)
        hour = morning_hour if index % 2 == 0 else evening_hour
        slot = datetime(
            publish_date.year,
            publish_date.month,
            publish_date.day,
            hour,
            0,
            0,
            tzinfo=KST,
        ).astimezone(UTC).isoformat()
        slots.append(slot)
        if index % 2 == 1:
            day_offset += 1

    return slots


def collect_pending_upload_entries(entries):
    pending = []

    for upload_key, value in (entries or {}).items():
        if not isinstance(value, dict):
            continue
        if not value.get("generated"):
            continue
        if value.get("uploaded"):
            continue

        pending.append({
            "upload_key": upload_key,
            "level": value.get("level"),
            "day": value.get("day"),
            "generated": bool(value.get("generated")),
            "uploaded": bool(value.get("uploaded")),
            "updated_at": value.get("updated_at"),
            "deferred_reason": value.get("deferred_reason"),
        })

    pending.sort(key=lambda item: ((item.get("updated_at") or ""), item.get("upload_key") or ""))
    return pending
