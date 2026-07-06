from __future__ import annotations

import os
from datetime import datetime

import requests

BOT_TOKEN = os.getenv("JLPT_BOT_TOKEN", "").strip()
ALLOWED_CHAT_ID = os.getenv("JLPT_BOT_ALLOWED_CHAT_ID", "").strip()


def _status_count(rows, target):
    return sum(1 for row in rows if row.get("status") == target)


def build_generation_summary_message(rows, backlog_ready_count=0):
    success_count = _status_count(rows, "generated")
    skipped_count = _status_count(rows, "skipped")
    failed_count = _status_count(rows, "failed")

    lines = [
        "?? ??? ??",
        f"- ?? {success_count}",
        f"- ?? {skipped_count}",
        f"- ?? {failed_count}",
        f"- ??? ?? {int(backlog_ready_count)}",
    ]

    detail_rows = [row for row in rows if row.get("status") == "failed"]
    if detail_rows:
        lines.append("")
        lines.append("?? ??")
        for row in detail_rows:
            lines.append(f"- {row.get('level')} DAY {row.get('day') or '-'}: {row.get('reason') or 'unknown'}")

    return "\n".join(lines)


def build_upload_summary_message(rows, backlog_count=0):
    success_count = _status_count(rows, "uploaded")
    deferred_count = _status_count(rows, "deferred")
    failed_count = _status_count(rows, "failed")

    lines = [
        "??? ??? ??",
        f"- ?? {success_count}",
        f"- ?? {deferred_count}",
        f"- ?? {failed_count}",
        f"- ?? ??? {int(backlog_count)}",
    ]

    success_rows = [row for row in rows if row.get("status") == "uploaded" and row.get("publish_at")]
    if success_rows:
        lines.append("")
        lines.append("?? ??")
        for row in success_rows:
            lines.append(f"- {row.get('level')} DAY {row.get('day')}: {row.get('publish_at')}")

    detail_rows = [row for row in rows if row.get("status") in {"deferred", "failed"}]
    if detail_rows:
        lines.append("")
        lines.append("?? ??")
        for row in detail_rows:
            suffix = row.get("publish_at") or "???"
            lines.append(f"- {row.get('level')} DAY {row.get('day')}: {row.get('reason') or row.get('status')} / {suffix}")

    return "\n".join(lines)


def send_telegram_text(text, bot_token=None, chat_id=None, timeout=30):
    token = (bot_token or BOT_TOKEN or "").strip()
    target_chat = str(chat_id or ALLOWED_CHAT_ID or "").strip()
    if not token or not target_chat:
        return False

    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data={
            "chat_id": target_chat,
            "text": str(text),
            "disable_web_page_preview": True,
        },
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    if not payload.get("ok"):
        raise RuntimeError(f"Telegram API error: {payload}")
    return True


def send_telegram_text_best_effort(text, bot_token=None, chat_id=None, timeout=30, logger=None):
    try:
        return send_telegram_text(text, bot_token=bot_token, chat_id=chat_id, timeout=timeout)
    except Exception as exc:
        if logger:
            logger(f"Telegram notification failed: {exc}")
        return False
