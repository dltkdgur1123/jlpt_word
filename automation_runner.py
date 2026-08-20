from __future__ import annotations

import os
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)
load_dotenv(BASE_DIR / ".env")

import main
from src.data.business_word_provider import get_remaining_item_counts as get_business_remaining_counts
from src.data.jlpt_word_provider import get_remaining_item_counts as get_jlpt_remaining_counts
from src.notifications.telegram_notifier import (
    build_generation_summary_message,
    build_upload_summary_message,
    send_telegram_text_best_effort,
)
from src.ops.automation_workflow import (
    AUTOMATION_LEVELS,
    build_publish_schedule,
    collect_pending_upload_entries,
    evaluate_generation_readiness,
    get_latest_reserved_publish_at,
)
from src.youtube.upload_log import list_upload_entries, update_uploaded_entry
from src.youtube.youtube_uploader import is_retryable_upload_error

DATA_DIR = BASE_DIR / "data"
GENERATION_LOG = DATA_DIR / "automation_generation.log"
UPLOAD_LOG = DATA_DIR / "automation_upload.log"
UPLOAD_GAP_SECONDS = int(os.getenv("AUTOMATION_UPLOAD_GAP_SECONDS", "15"))


def log_line(log_path: Path, text: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    with log_path.open("a", encoding="utf-8") as file:
        file.write(f"[{timestamp}] {text}\n")


def short_error_text(error: Exception) -> str:
    return " ".join(str(error).strip().split())[:300] or error.__class__.__name__



def resolve_remaining_counts(level: str):
    if str(level).strip().upper() == "BUSINESS":
        return get_business_remaining_counts()
    return get_jlpt_remaining_counts(level)



def run_generation() -> int:
    results = []

    for level in AUTOMATION_LEVELS:
        try:
            counts = resolve_remaining_counts(level)
            readiness = evaluate_generation_readiness(level, counts)
            if not readiness["ready"]:
                results.append({
                    "level": level,
                    "status": "skipped",
                    "reason": readiness["reason"],
                })
                log_line(GENERATION_LOG, f"SKIP {level}: {readiness['reason']} {counts}")
                continue

            day_text = main.generate_pipeline(level)
            results.append({
                "level": level,
                "status": "generated",
                "day": day_text,
            })
            log_line(GENERATION_LOG, f"GENERATED {level} DAY {day_text}")
        except Exception as error:
            reason = short_error_text(error)
            results.append({
                "level": level,
                "status": "failed",
                "reason": reason,
            })
            log_line(GENERATION_LOG, f"FAILED {level}: {reason}")
            traceback.print_exc()

    backlog_ready_count = len(collect_pending_upload_entries(list_upload_entries()))
    message = build_generation_summary_message(results, backlog_ready_count=backlog_ready_count)
    send_telegram_text_best_effort(message, logger=lambda msg: log_line(GENERATION_LOG, msg))

    return 1 if any(row.get("status") == "failed" for row in results) else 0



def mark_deferred(upload_key: str, reason: str, publish_at: str | None = None) -> None:
    update_uploaded_entry(
        upload_key,
        uploaded=False,
        queued_for_upload=True,
        automation_status="deferred",
        deferred_reason=reason,
        planned_publish_at=publish_at,
        last_upload_attempt_at=datetime.now(timezone.utc).isoformat(),
    )



def run_upload() -> int:
    entries = list_upload_entries()
    pending = collect_pending_upload_entries(entries)

    if not pending:
        message = build_upload_summary_message([], backlog_count=0)
        send_telegram_text_best_effort(message, logger=lambda msg: log_line(UPLOAD_LOG, msg))
        return 0

    latest_publish_at = get_latest_reserved_publish_at(entries)
    publish_slots = build_publish_schedule(len(pending), latest_publish_at=latest_publish_at)
    results = []

    for index, entry in enumerate(pending):
        level = str(entry.get("level") or "").strip().upper()
        day = str(entry.get("day") or "").strip().zfill(3)
        upload_key = entry.get("upload_key")
        publish_at = publish_slots[index]

        if not level or not day or not upload_key:
            continue

        update_uploaded_entry(
            upload_key,
            queued_for_upload=True,
            automation_status="uploading",
            planned_publish_at=publish_at,
            deferred_reason=None,
        )

        try:
            main.upload_existing_day(level, day=day, privacy_status="private", publish_at=publish_at)
            main.finalize_uploaded_day(level, day=day, delete_local=False, cleanup_intermediate=True)
            update_uploaded_entry(
                upload_key,
                queued_for_upload=False,
                automation_status="uploaded",
                deferred_reason=None,
                planned_publish_at=publish_at,
            )
            results.append({
                "level": level,
                "day": day,
                "status": "uploaded",
                "publish_at": publish_at,
            })
            log_line(UPLOAD_LOG, f"UPLOADED {upload_key} -> {publish_at}")
            if index < len(pending) - 1 and UPLOAD_GAP_SECONDS > 0:
                time.sleep(UPLOAD_GAP_SECONDS)
        except Exception as error:
            reason = short_error_text(error)
            traceback.print_exc()
            if is_retryable_upload_error(error):
                mark_deferred(upload_key, reason, publish_at=publish_at)
                results.append({
                    "level": level,
                    "day": day,
                    "status": "deferred",
                    "reason": reason,
                    "publish_at": publish_at,
                })
                log_line(UPLOAD_LOG, f"DEFERRED {upload_key}: {reason}")

                for remaining_index in range(index + 1, len(pending)):
                    remaining = pending[remaining_index]
                    remaining_key = remaining.get("upload_key")
                    remaining_publish_at = publish_slots[remaining_index]
                    if remaining_key:
                        mark_deferred(remaining_key, "stopped_after_retryable_error", publish_at=remaining_publish_at)
                    results.append({
                        "level": remaining.get("level"),
                        "day": remaining.get("day"),
                        "status": "deferred",
                        "reason": "stopped_after_retryable_error",
                        "publish_at": remaining_publish_at,
                    })
                break

            update_uploaded_entry(
                upload_key,
                uploaded=False,
                queued_for_upload=True,
                automation_status="failed",
                deferred_reason=reason,
                planned_publish_at=publish_at,
                last_upload_attempt_at=datetime.now(timezone.utc).isoformat(),
            )
            results.append({
                "level": level,
                "day": day,
                "status": "failed",
                "reason": reason,
                "publish_at": publish_at,
            })
            log_line(UPLOAD_LOG, f"FAILED {upload_key}: {reason}")

    backlog_count = len(collect_pending_upload_entries(list_upload_entries()))
    message = build_upload_summary_message(results, backlog_count=backlog_count)
    send_telegram_text_best_effort(message, logger=lambda msg: log_line(UPLOAD_LOG, msg))

    if any(row.get("status") in {"failed", "deferred"} for row in results):
        return 1
    return 0



def main_cli(argv=None) -> int:
    args = list(argv or sys.argv[1:])
    if not args:
        print("usage: python automation_runner.py [generate|upload]")
        return 2

    command = args[0].strip().lower()
    if command == "generate":
        return run_generation()
    if command == "upload":
        return run_upload()

    print(f"unsupported command: {command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main_cli())
