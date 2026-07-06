import json
import os
import sys
import threading
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv

from bot_ai import AIChatClient, parse_jlpt_natural_command


BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)

load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("JLPT_BOT_TOKEN", "").strip()
ALLOWED_CHAT_ID = os.getenv("JLPT_BOT_ALLOWED_CHAT_ID", "").strip()
POLL_TIMEOUT = int(os.getenv("JLPT_BOT_POLL_TIMEOUT", "30"))

API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"
DAY_STATUS_PATH = BASE_DIR / "data" / "day_status.json"
DAY_VIDEO_DIR = BASE_DIR / "output" / "day_videos"

JLPT_LEVELS = ["N1", "N2", "N3", "N4", "N5"]
BUSINESS_LEVEL = "BUSINESS"
ALL_LEVELS = JLPT_LEVELS + [BUSINESS_LEVEL]
ALL_LEVEL_ALIASES = {"all_level", "all", "all_levels"}
KST = ZoneInfo("Asia/Seoul")
UTC = ZoneInfo("UTC")

job_lock = threading.Lock()

ai_client = AIChatClient(
    history_path=BASE_DIR / "data" / "jlpt_chat_history.json",
    bot_name="JLPT 생성봇",
    domain="JLPT 일본어 학습, 영상 생성 및 YouTube 업로드",
    capabilities=(
        "N1~N5 및 BUSINESS 영상 생성, DAY 상태 확인, 기존 영상 업로드, "
        "예약 업로드, 업로드 후 백업/정리, 자연어 명령 처리"
    ),
)


def api_call(method, payload=None, files=None, timeout=120):
    if not BOT_TOKEN:
        raise RuntimeError("JLPT_BOT_TOKEN is not set in .env")

    response = requests.post(
        f"{API_BASE}/{method}",
        data=payload or {},
        files=files,
        timeout=timeout,
    )
    response.raise_for_status()
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram API error: {data}")
    return data["result"]


def send_message(chat_id, text, reply_markup=None, parse_mode="Markdown"):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup, ensure_ascii=False)

    return api_call(
        "sendMessage",
        payload,
    )


def send_plain_text(chat_id, text):
    value = str(text or "").strip() or "응답 내용이 없습니다."
    while value:
        chunk = value[:3900]
        value = value[3900:]
        send_message(chat_id, chunk, parse_mode=None)


def answer_callback_query(callback_query_id, text=None):
    payload = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text
    return api_call("answerCallbackQuery", payload)


def send_video_or_document(chat_id, video_path):
    video_path = Path(video_path)
    if not video_path.exists():
        send_message(chat_id, f"영상 파일을 찾지 못했습니다:\n`{video_path}`")
        return

    caption = video_path.name
    try:
        with video_path.open("rb") as file_obj:
            api_call(
                "sendVideo",
                {"chat_id": chat_id, "caption": caption},
                {"video": file_obj},
                timeout=600,
            )
    except Exception:
        with video_path.open("rb") as file_obj:
            api_call(
                "sendDocument",
                {"chat_id": chat_id, "caption": caption},
                {"document": file_obj},
                timeout=600,
            )


def normalize_level(value):
    level = str(value or "").strip().upper()
    if level in ALL_LEVELS:
        return level
    return None


def normalize_day(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text.isdigit():
        return None
    return text.zfill(3)


def strip_bot_mention(value):
    return str(value or "").strip().split("@")[0]


def load_day_status():
    if not DAY_STATUS_PATH.exists():
        return {}
    return json.loads(DAY_STATUS_PATH.read_text(encoding="utf-8"))


def build_status_text():
    status = load_day_status()
    if not status:
        return "DAY 상태 파일을 찾지 못했습니다."

    lines = ["*JLPT 생성봇 상태*"]
    for level in ALL_LEVELS:
        day = status.get(level, "-")
        lines.append(f"- `{level}`: DAY `{str(day).zfill(3) if isinstance(day, int) else day}`")
    return "\n".join(lines)


def get_day_video_path(level, day_text):
    return DAY_VIDEO_DIR / level / f"{level}_DAY_{day_text}.mp4"


def build_publish_at_from_kst(date_text, time_text):
    try:
        date_part = str(date_text).strip()
        time_part = str(time_text).strip()
        if len(time_part) == 4 and time_part.isdigit():
            time_part = f"{time_part[:2]}:{time_part[2:]}"
        dt = datetime.fromisoformat(f"{date_part} {time_part}")
        return dt.replace(tzinfo=KST).astimezone(UTC).isoformat()
    except Exception as exc:
        raise ValueError("날짜/시간 형식은 `2026-07-01 18:00`처럼 입력해 주세요.") from exc


def build_publish_at_for_fixed_time(date_text, hour):
    return build_publish_at_from_kst(date_text, f"{int(hour):02d}:00")


def load_upload_entries():
    log_path = BASE_DIR / "data" / "uploaded_log.json"
    if not log_path.exists():
        return {}
    return json.loads(log_path.read_text(encoding="utf-8"))


def get_latest_publish_at_kst():
    latest = None
    for entry in load_upload_entries().values():
        if not isinstance(entry, dict):
            continue
        publish_at = entry.get("publish_at")
        if not publish_at:
            continue
        try:
            dt = datetime.fromisoformat(str(publish_at).replace("Z", "+00:00")).astimezone(KST)
        except ValueError:
            continue
        if latest is None or dt > latest:
            latest = dt
    return latest


def get_recommended_publish_date(hour):
    latest = get_latest_publish_at_kst()
    if latest is None:
        return datetime.now(KST).date().isoformat()

    candidate = latest.replace(hour=int(hour), minute=0, second=0, microsecond=0)
    if candidate <= latest:
        candidate = candidate + timedelta(days=1)
    return candidate.date().isoformat()


def run_job(chat_id, title, target):
    if not job_lock.acquire(blocking=False):
        send_message(chat_id, "이미 다른 생성/업로드 작업이 실행 중입니다. 완료 후 다시 시도해 주세요.")
        return

    try:
        send_message(chat_id, f"작업 시작: *{title}*")
        target()
        send_message(chat_id, f"작업 완료: *{title}*")
    except Exception as exc:
        error_text = "".join(traceback.format_exception_only(type(exc), exc)).strip()
        send_message(chat_id, f"작업 실패: *{title}*\n`{error_text}`")
        traceback.print_exc()
    finally:
        job_lock.release()


def start_background_job(chat_id, title, target):
    thread = threading.Thread(target=run_job, args=(chat_id, title, target), daemon=True)
    thread.start()


def start_ai_chat(chat_id, user_text):
    def worker():
        try:
            answer = ai_client.reply(chat_id, user_text)
        except Exception as exc:
            traceback.print_exc()
            answer = f"AI 대화 중 오류가 발생했습니다: {exc}"
        send_plain_text(chat_id, answer)

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()


def make_level(chat_id, level):
    import main

    day_text = main.generate_pipeline(level)
    video_path = get_day_video_path(level, day_text)
    send_message(chat_id, f"`{level}` DAY `{day_text}` 생성 완료. 영상 전송을 시도합니다.")
    send_video_or_document(chat_id, video_path)


def make_all(chat_id):
    import main

    results = []
    for level in JLPT_LEVELS:
        send_message(chat_id, f"`{level}` 생성 시작")
        day_text = main.generate_pipeline(level)
        results.append(f"{level} DAY {day_text}")
    send_message(chat_id, "전체 생성 완료:\n" + "\n".join(f"- `{item}`" for item in results))


def upload_all_latest(chat_id, publish_at=None):
    import main

    results = []
    for level in JLPT_LEVELS:
        day_text = main.get_latest_generated_day(level)
        if publish_at:
            send_message(chat_id, f"`{level}` DAY `{day_text}` 예약 업로드 시작\nAPI 시간: `{publish_at}`")
        else:
            send_message(chat_id, f"`{level}` DAY `{day_text}` 업로드 시작")
        uploaded_day = main.upload_existing_day(level, day_text, privacy_status="private", publish_at=publish_at)
        results.append(f"{level} DAY {uploaded_day}")
    if publish_at:
        send_message(chat_id, "전체 예약 업로드 완료:\n" + "\n".join(f"- `{item}`" for item in results))
    else:
        send_message(chat_id, "전체 업로드 완료:\n" + "\n".join(f"- `{item}`" for item in results))


def upload_latest_level(chat_id, level, publish_at=None):
    import main

    day_text = main.get_latest_generated_day(level)
    upload_level_day(chat_id, level, day_text, publish_at=publish_at)


def upload_business_latest(chat_id, publish_at=None):
    import main

    day_text = main.get_latest_generated_day(BUSINESS_LEVEL)
    if publish_at:
        send_message(chat_id, f"`BUSINESS` DAY `{day_text}` 예약 업로드 시작\nAPI 시간: `{publish_at}`")
    else:
        send_message(chat_id, f"`BUSINESS` DAY `{day_text}` 업로드 시작")
    uploaded_day = main.upload_existing_day(BUSINESS_LEVEL, day_text, privacy_status="private", publish_at=publish_at)
    if publish_at:
        send_message(chat_id, f"`BUSINESS` DAY `{uploaded_day}` 예약 업로드 완료.\nAPI 시간: `{publish_at}`")
    else:
        send_message(chat_id, f"`BUSINESS` DAY `{uploaded_day}` 업로드 완료.")


def upload_level_day(chat_id, level, day_text, publish_at=None):
    import main

    uploaded_day = main.upload_existing_day(level, day_text, privacy_status="private", publish_at=publish_at)
    if publish_at:
        send_message(chat_id, f"`{level}` DAY `{uploaded_day}` 예약 업로드 완료.\nAPI 시간: `{publish_at}`")
    else:
        send_message(chat_id, f"`{level}` DAY `{uploaded_day}` YouTube 업로드 완료.")


def finalize_level_day(chat_id, level, day_text):
    import main

    result = main.finalize_uploaded_day(level, day_text, delete_local=True, cleanup_intermediate=True)
    send_message(chat_id, f"`{level}` DAY `{result.get('day')}` 백업/정리 완료.")


def help_text():
    return "\n".join(
        [
            "*JLPT 생성봇 명령어*",
            "- `/menu` 버튼 메뉴 열기",
            "- `/1` N1~N5 전체 생성",
            "- `/2 2026-07-01` N1~N5 전체 오전 8시 예약 업로드",
            "- `/3 2026-07-01` N1~N5 전체 오후 6시 예약 업로드",
            "- `/status` 현재 DAY 확인",
            "- `/make N5` 해당 레벨 DAY 쇼츠 생성",
            "- `/make all_level` N1~N5 전체 생성",
            "- `/business` 비즈니스 일본어 DAY 생성",
            "- `/upload all_level` N1~N5 최신 생성본 전체 업로드",
            "- `/upload N5 045` 기존 DAY 영상 YouTube 업로드",
            "- `/upload_at BUSINESS 018 2026-07-01 18:00` 지정 시간 예약 업로드",
            "- `/upload_at all_level 2026-07-01 18:00` N1~N5 전체 지정 시간 예약 업로드",
            "- `/upload_morning BUSINESS 018 2026-07-01` 오전 8시 예약 업로드",
            "- `/upload_evening BUSINESS 018 2026-07-01` 오후 6시 예약 업로드",
            "- `/upload_morning all_level 2026-07-01` N1~N5 전체 오전 8시 예약 업로드",
            "- `/upload_evening all_level 2026-07-01` N1~N5 전체 오후 6시 예약 업로드",
            "- `/finalize N5 045` 업로드된 DAY 백업/정리",
            "- `/help` 도움말",
            "- `/clear` AI 대화 기록 초기화",
            "",
            "자연어 예시: `N2 영상 만들어줘`, `내일 오후 6시에 전체 업로드해줘`",
            "일반 질문과 대화도 가능합니다.",
            "",
            "주의: 생성/업로드 작업은 한 번에 하나만 실행됩니다.",
        ]
    )


def menu_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "1. N1~N5 전체 생성", "callback_data": "menu:make_all"}],
            [{"text": "2. BUSINESS 생성", "callback_data": "menu:make_business"}],
            [{"text": "3. 특정 레벨 선택 생성", "callback_data": "menu:choose_level"}],
            [{"text": "4. 최신본 예약 업로드", "callback_data": "menu:choose_upload_target"}],
            [{"text": "상태 확인", "callback_data": "menu:status"}],
        ]
    }


def level_keyboard():
    return {
        "inline_keyboard": [
            [
                {"text": "N1", "callback_data": "menu:make:N1"},
                {"text": "N2", "callback_data": "menu:make:N2"},
                {"text": "N3", "callback_data": "menu:make:N3"},
            ],
            [
                {"text": "N4", "callback_data": "menu:make:N4"},
                {"text": "N5", "callback_data": "menu:make:N5"},
            ],
            [{"text": "← 처음 메뉴", "callback_data": "menu:home"}],
        ]
    }


def upload_target_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "N1~N5 전체 최신본", "callback_data": "menu:upload_time:ALL"}],
            [{"text": "BUSINESS 최신본", "callback_data": "menu:upload_time:BUSINESS"}],
            [{"text": "← 처음 메뉴", "callback_data": "menu:home"}],
        ]
    }


def upload_time_keyboard(target):
    morning_date = get_recommended_publish_date(8)
    evening_date = get_recommended_publish_date(18)
    return {
        "inline_keyboard": [
            [{"text": f"1. 오전 8시 ({morning_date})", "callback_data": f"menu:upload:{target}:8:{morning_date}"}],
            [{"text": f"2. 오후 6시 ({evening_date})", "callback_data": f"menu:upload:{target}:18:{evening_date}"}],
            [{"text": "← 업로드 대상 선택", "callback_data": "menu:choose_upload_target"}],
        ]
    }


def send_menu(chat_id):
    latest = get_latest_publish_at_kst()
    latest_text = latest.strftime("%Y-%m-%d %H:%M KST") if latest else "기록 없음"
    send_message(
        chat_id,
        "\n".join(
            [
                "*JLPT 생성봇 메뉴*",
                "",
                "원하는 작업을 선택하세요.",
                f"최신 예약 업로드 기준: `{latest_text}`",
            ]
        ),
        reply_markup=menu_keyboard(),
    )


def handle_callback_query(callback_query):
    callback_query_id = callback_query.get("id")
    message = callback_query.get("message") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    data = callback_query.get("data") or ""

    if callback_query_id:
        answer_callback_query(callback_query_id)

    if not chat_id or not is_allowed_chat(chat_id):
        return

    if data == "menu:home":
        send_menu(chat_id)
        return
    if data == "menu:status":
        send_message(chat_id, build_status_text())
        return
    if data == "menu:make_all":
        start_background_job(chat_id, "N1~N5 전체 생성", lambda: make_all(chat_id))
        return
    if data == "menu:make_business":
        start_background_job(chat_id, "BUSINESS DAY 생성", lambda: make_level(chat_id, BUSINESS_LEVEL))
        return
    if data == "menu:choose_level":
        send_message(chat_id, "*생성할 레벨을 선택하세요.*", reply_markup=level_keyboard())
        return
    if data.startswith("menu:make:"):
        level = normalize_level(data.split(":")[-1])
        if level and level != BUSINESS_LEVEL:
            start_background_job(chat_id, f"{level} DAY 생성", lambda: make_level(chat_id, level))
        return
    if data == "menu:choose_upload_target":
        send_message(chat_id, "*예약 업로드할 최신본 대상을 선택하세요.*", reply_markup=upload_target_keyboard())
        return
    if data.startswith("menu:upload_time:"):
        target = data.split(":")[-1]
        send_message(chat_id, "*업로드 시간을 선택하세요.*\n날짜는 최신 예약 업로드 기준으로 자동 계산됩니다.", reply_markup=upload_time_keyboard(target))
        return
    if data.startswith("menu:upload:"):
        _, _, target, hour, date_text = data.split(":")
        publish_at = build_publish_at_for_fixed_time(date_text, int(hour))
        label = "오전 8시" if int(hour) == 8 else "오후 6시"
        if target == "ALL":
            start_background_job(
                chat_id,
                f"N1~N5 전체 {date_text} {label} 예약 업로드",
                lambda: upload_all_latest(chat_id, publish_at=publish_at),
            )
        elif target == BUSINESS_LEVEL:
            start_background_job(
                chat_id,
                f"BUSINESS {date_text} {label} 예약 업로드",
                lambda: upload_business_latest(chat_id, publish_at=publish_at),
            )
        return


def is_allowed_chat(chat_id):
    if not ALLOWED_CHAT_ID:
        return True
    return str(chat_id) == ALLOWED_CHAT_ID


def handle_message(message):
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    text = (message.get("text") or "").strip()

    if not chat_id or not text:
        return

    if not is_allowed_chat(chat_id):
        send_message(chat_id, "이 봇은 허용된 채팅방에서만 사용할 수 있습니다.")
        return

    command = text.split()[0].split("@")[0].lower()
    args = text.split()[1:]

    if command in {"/start", "/menu"}:
        send_menu(chat_id)
        return

    if command == "/help":
        send_message(chat_id, help_text())
        return

    if command in {"/clear", "/clear_chat"}:
        ai_client.clear(chat_id)
        send_message(chat_id, "AI 대화 기록을 초기화했습니다.", parse_mode=None)
        return

    if command == "/1":
        start_background_job(chat_id, "N1~N5 전체 생성", lambda: make_all(chat_id))
        return

    if command == "/2":
        date_text = args[0] if args else None
        if not date_text:
            send_message(chat_id, "사용법: `/2 2026-07-01`\n의미: N1~N5 전체 오전 8시 예약 업로드")
            return
        publish_at = build_publish_at_for_fixed_time(date_text, 8)
        start_background_job(
            chat_id,
            "N1~N5 전체 오전 8시 예약 업로드",
            lambda: upload_all_latest(chat_id, publish_at=publish_at),
        )
        return

    if command == "/3":
        date_text = args[0] if args else None
        if not date_text:
            send_message(chat_id, "사용법: `/3 2026-07-01`\n의미: N1~N5 전체 오후 6시 예약 업로드")
            return
        publish_at = build_publish_at_for_fixed_time(date_text, 18)
        start_background_job(
            chat_id,
            "N1~N5 전체 오후 6시 예약 업로드",
            lambda: upload_all_latest(chat_id, publish_at=publish_at),
        )
        return

    if command == "/status":
        send_message(chat_id, build_status_text())
        return

    if command == "/make":
        first_arg = strip_bot_mention(args[0]).lower() if args else ""
        if first_arg in ALL_LEVEL_ALIASES:
            start_background_job(chat_id, "N1~N5 전체 생성", lambda: make_all(chat_id))
            return
        level = normalize_level(args[0] if args else None)
        if not level or level == BUSINESS_LEVEL:
            send_message(chat_id, "사용법: `/make N5` 또는 `/make all_level`")
            return
        start_background_job(chat_id, f"{level} DAY 생성", lambda: make_level(chat_id, level))
        return

    if command == "/business":
        start_background_job(chat_id, "BUSINESS DAY 생성", lambda: make_level(chat_id, BUSINESS_LEVEL))
        return

    if command == "/make_all":
        start_background_job(chat_id, "N1~N5 전체 생성", lambda: make_all(chat_id))
        return

    if command == "/upload_latest":
        level = normalize_level(args[0] if args else None)
        if not level:
            send_message(chat_id, "사용법: `/upload_latest N5`")
            return
        if level == BUSINESS_LEVEL:
            start_background_job(
                chat_id,
                "BUSINESS 최신 생성본 업로드",
                lambda: upload_business_latest(chat_id),
            )
        else:
            start_background_job(
                chat_id,
                f"{level} 최신 생성본 업로드",
                lambda: upload_latest_level(chat_id, level),
            )
        return

    if command == "/upload":
        first_arg = strip_bot_mention(args[0]).lower() if args else ""
        if first_arg in ALL_LEVEL_ALIASES:
            start_background_job(chat_id, "N1~N5 최신 생성본 전체 업로드", lambda: upload_all_latest(chat_id))
            return
        level = normalize_level(args[0] if len(args) >= 1 else None)
        day_text = normalize_day(args[1] if len(args) >= 2 else None)
        if not level or not day_text:
            send_message(chat_id, "사용법: `/upload N5 045` 또는 `/upload all_level`")
            return
        start_background_job(
            chat_id,
            f"{level} DAY {day_text} 업로드",
            lambda: upload_level_day(chat_id, level, day_text),
        )
        return

    if command == "/upload_at":
        first_arg = strip_bot_mention(args[0]).lower() if args else ""
        if first_arg in ALL_LEVEL_ALIASES:
            date_text = args[1] if len(args) >= 2 else None
            time_text = args[2] if len(args) >= 3 else None
            if not date_text or not time_text:
                send_message(chat_id, "사용법: `/upload_at all_level 2026-07-01 18:00`")
                return
            try:
                publish_at = build_publish_at_from_kst(date_text, time_text)
            except ValueError as exc:
                send_message(chat_id, str(exc))
                return
            start_background_job(
                chat_id,
                "N1~N5 전체 지정 시간 예약 업로드",
                lambda: upload_all_latest(chat_id, publish_at=publish_at),
            )
            return

        level = normalize_level(args[0] if len(args) >= 1 else None)
        day_text = normalize_day(args[1] if len(args) >= 2 else None)
        date_text = args[2] if len(args) >= 3 else None
        time_text = args[3] if len(args) >= 4 else None
        if not level or not day_text or not date_text or not time_text:
            send_message(chat_id, "사용법: `/upload_at BUSINESS 018 2026-07-01 18:00`")
            return
        try:
            publish_at = build_publish_at_from_kst(date_text, time_text)
        except ValueError as exc:
            send_message(chat_id, str(exc))
            return
        start_background_job(
            chat_id,
            f"{level} DAY {day_text} 예약 업로드",
            lambda: upload_level_day(chat_id, level, day_text, publish_at=publish_at),
        )
        return

    if command in {"/upload_morning", "/upload_8"}:
        first_arg = strip_bot_mention(args[0]).lower() if args else ""
        if first_arg in ALL_LEVEL_ALIASES:
            date_text = args[1] if len(args) >= 2 else None
            if not date_text:
                send_message(chat_id, "사용법: `/upload_morning all_level 2026-07-01`")
                return
            publish_at = build_publish_at_for_fixed_time(date_text, 8)
            start_background_job(
                chat_id,
                "N1~N5 전체 오전 8시 예약 업로드",
                lambda: upload_all_latest(chat_id, publish_at=publish_at),
            )
            return

        level = normalize_level(args[0] if len(args) >= 1 else None)
        day_text = normalize_day(args[1] if len(args) >= 2 else None)
        date_text = args[2] if len(args) >= 3 else None
        if not level or not day_text or not date_text:
            send_message(chat_id, "사용법: `/upload_morning BUSINESS 018 2026-07-01`")
            return
        publish_at = build_publish_at_for_fixed_time(date_text, 8)
        start_background_job(
            chat_id,
            f"{level} DAY {day_text} 오전 8시 예약 업로드",
            lambda: upload_level_day(chat_id, level, day_text, publish_at=publish_at),
        )
        return

    if command in {"/upload_evening", "/upload_18"}:
        first_arg = strip_bot_mention(args[0]).lower() if args else ""
        if first_arg in ALL_LEVEL_ALIASES:
            date_text = args[1] if len(args) >= 2 else None
            if not date_text:
                send_message(chat_id, "사용법: `/upload_evening all_level 2026-07-01`")
                return
            publish_at = build_publish_at_for_fixed_time(date_text, 18)
            start_background_job(
                chat_id,
                "N1~N5 전체 오후 6시 예약 업로드",
                lambda: upload_all_latest(chat_id, publish_at=publish_at),
            )
            return

        level = normalize_level(args[0] if len(args) >= 1 else None)
        day_text = normalize_day(args[1] if len(args) >= 2 else None)
        date_text = args[2] if len(args) >= 3 else None
        if not level or not day_text or not date_text:
            send_message(chat_id, "사용법: `/upload_evening BUSINESS 018 2026-07-01`")
            return
        publish_at = build_publish_at_for_fixed_time(date_text, 18)
        start_background_job(
            chat_id,
            f"{level} DAY {day_text} 오후 6시 예약 업로드",
            lambda: upload_level_day(chat_id, level, day_text, publish_at=publish_at),
        )
        return

    if command == "/finalize":
        level = normalize_level(args[0] if len(args) >= 1 else None)
        day_text = normalize_day(args[1] if len(args) >= 2 else None)
        if not level or not day_text:
            send_message(chat_id, "사용법: `/finalize N5 045`")
            return
        start_background_job(
            chat_id,
            f"{level} DAY {day_text} 백업/정리",
            lambda: finalize_level_day(chat_id, level, day_text),
        )
        return


    if not text.startswith("/"):
        parsed = parse_jlpt_natural_command(text)
        if parsed.message:
            send_message(chat_id, parsed.message, parse_mode=None)
            return
        if parsed.command:
            send_message(
                chat_id,
                f"자연어 명령을 `{parsed.command}`로 이해했습니다.",
            )
            forwarded = dict(message)
            forwarded["text"] = parsed.command
            handle_message(forwarded)
            return

        start_ai_chat(chat_id, text)
        return

    send_message(chat_id, "지원하지 않는 명령어입니다. `/help`를 확인하세요.")


def polling_loop():
    print("JLPT Telegram bot server started.")
    offset = None
    while True:
        try:
            result = requests.get(
                f"{API_BASE}/getUpdates",
                params={"timeout": POLL_TIMEOUT, "offset": offset},
                timeout=POLL_TIMEOUT + 10,
            )
            result.raise_for_status()
            updates = result.json().get("result", [])
            for update in updates:
                offset = update["update_id"] + 1
                callback_query = update.get("callback_query")
                if callback_query:
                    handle_callback_query(callback_query)
                    continue
                message = update.get("message") or update.get("edited_message")
                if message:
                    handle_message(message)
        except KeyboardInterrupt:
            print("JLPT Telegram bot server stopped.")
            break
        except Exception:
            traceback.print_exc()
            time.sleep(5)


if __name__ == "__main__":
    if not BOT_TOKEN:
        print("ERROR: JLPT_BOT_TOKEN is not set in .env")
        sys.exit(1)
    polling_loop()
