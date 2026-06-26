# ==================================================
# 파일명: upload_log.py
# 역할: 업로드 완료 기록 저장
# ==================================================


# ==================================================
# 1. 라이브러리 import
# ==================================================

import json
import os
from datetime import datetime, timezone


# ==================================================
# 2. 로그 파일 경로
# ==================================================

LOG_FILE = "data/uploaded_log.json"


# ==================================================
# 3. 로그 읽기
# ==================================================

def load_upload_log():

    if not os.path.exists(LOG_FILE):
        return {}

    with open(LOG_FILE, "r", encoding="utf-8")as file:
        return json.load(file)


def _normalize_entry(key, value):
    if isinstance(value, dict):
        entry = dict(value)
        entry.setdefault("uploaded", True)
        entry.setdefault("upload_key", key)
        return entry

    return {
        "upload_key": key,
        "uploaded": bool(value),
    }


def get_upload_entry(key):
    log = load_upload_log()
    value = log.get(key)
    if value is None:
        return None

    return _normalize_entry(key, value)


def list_upload_entries():
    log = load_upload_log()
    return {
        key: _normalize_entry(key, value)
        for key, value in log.items()
    }


# ==================================================
# 4. 업로드 여부 확인
# ==================================================

def is_uploaded(key):
    entry = get_upload_entry(key)
    return bool(entry and entry.get("uploaded"))


# ==================================================
# 5. 업로드 완료 저장
# ==================================================

def save_uploaded(key, video_id=None, level=None, day=None, privacy_status=None, publish_at=None, title=None):
    log = load_upload_log()
    previous = _normalize_entry(key, log[key]) if key in log else {"upload_key": key}

    entry = {
        **previous,
        "upload_key": key,
        "uploaded": True,
        "video_id": video_id or previous.get("video_id"),
        "level": level or previous.get("level"),
        "day": day or previous.get("day"),
        "privacy_status": privacy_status or previous.get("privacy_status"),
        "publish_at": publish_at if publish_at is not None else previous.get("publish_at"),
        "title": title or previous.get("title"),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    entry.setdefault("uploaded_at", entry["updated_at"])
    log[key] = entry

    with open(LOG_FILE, "w", encoding="utf-8") as file:
        json.dump(log, file, ensure_ascii=False, indent=4)


def update_uploaded_entry(key, **updates):
    log = load_upload_log()
    previous = _normalize_entry(key, log[key]) if key in log else {"upload_key": key, "uploaded": False}

    entry = {
        **previous,
        **updates,
        "upload_key": key,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    log[key] = entry

    with open(LOG_FILE, "w", encoding="utf-8") as file:
        json.dump(log, file, ensure_ascii=False, indent=4)
