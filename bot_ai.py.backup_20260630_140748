from __future__ import annotations

import json
import os
import re
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

import requests

KST = ZoneInfo("Asia/Seoul")
OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"


@dataclass(frozen=True)
class NaturalCommandResult:
    command: Optional[str] = None
    message: Optional[str] = None


class JsonConversationStore:
    def __init__(self, path: Path | str, max_messages: int = 12):
        self.path = Path(path)
        self.max_messages = max(2, int(max_messages))
        self._lock = threading.Lock()

    def _load_unlocked(self) -> dict[str, list[dict[str, str]]]:
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return data if isinstance(data, dict) else {}

    def _save_unlocked(self, data: dict[str, list[dict[str, str]]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        temp_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp_path.replace(self.path)

    def get(self, chat_id: str | int) -> list[dict[str, str]]:
        key = str(chat_id)
        with self._lock:
            history = self._load_unlocked().get(key, [])
            if not isinstance(history, list):
                return []
            return [item for item in history if isinstance(item, dict)][-self.max_messages :]

    def append(self, chat_id: str | int, role: str, content: str) -> None:
        key = str(chat_id)
        item = {"role": str(role), "content": str(content)}
        with self._lock:
            data = self._load_unlocked()
            history = data.get(key, [])
            if not isinstance(history, list):
                history = []
            history.append(item)
            data[key] = history[-self.max_messages :]
            self._save_unlocked(data)

    def clear(self, chat_id: str | int) -> None:
        key = str(chat_id)
        with self._lock:
            data = self._load_unlocked()
            data.pop(key, None)
            self._save_unlocked(data)


def extract_output_text(payload: dict) -> str:
    direct = payload.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()

    chunks: list[str] = []
    for item in payload.get("output", []) or []:
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        for content in item.get("content", []) or []:
            if not isinstance(content, dict):
                continue
            if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                chunks.append(content["text"])
    return "".join(chunks).strip()


class AIChatClient:
    def __init__(
        self,
        history_path: Path | str,
        bot_name: str,
        domain: str,
        capabilities: str,
        model: Optional[str] = None,
    ):
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.model = (
            model
            or os.getenv("BOT_CHAT_MODEL", "").strip()
            or os.getenv("OPENAI_CHAT_MODEL", "").strip()
            or os.getenv("OPENAI_MODEL", "").strip()
            or "gpt-5.4-mini"
        )
        self.max_output_tokens = int(os.getenv("BOT_CHAT_MAX_OUTPUT_TOKENS", "700"))
        self.timeout = int(os.getenv("BOT_CHAT_TIMEOUT", "120"))
        self.store = JsonConversationStore(
            history_path,
            max_messages=int(os.getenv("BOT_CHAT_HISTORY_MESSAGES", "12")),
        )
        self.instructions = (
            f"너는 {bot_name}이다. 주 분야는 {domain}이다. "
            "사용자에게 기본적으로 한국어로 간결하고 정확하게 답한다. "
            "일본어 또는 다른 언어로 질문받으면 필요한 범위에서 해당 언어도 사용할 수 있다. "
            f"이 봇이 실제로 수행할 수 있는 기능은 다음과 같다: {capabilities}. "
            "영상 생성이나 업로드가 실제로 실행되었다고 거짓으로 말하지 않는다. "
            "실행 명령은 별도 명령 라우터가 처리하므로, 일반 대화에서는 질문에 답하고 사용법을 설명한다. "
            "실시간 웹 검색 기능은 없으므로 최신 정보가 필요할 때는 그 한계를 짧게 밝힌다."
        )

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def clear(self, chat_id: str | int) -> None:
        self.store.clear(chat_id)

    def reply(self, chat_id: str | int, user_text: str) -> str:
        if not self.available:
            return (
                "일반 AI 대화를 사용하려면 프로젝트 `.env`에 "
                "`OPENAI_API_KEY=...`를 설정해 주세요. 메뉴와 자연어 생성 명령은 계속 사용할 수 있습니다."
            )

        history = self.store.get(chat_id)
        input_messages = history + [{"role": "user", "content": user_text}]
        response = requests.post(
            OPENAI_RESPONSES_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "instructions": self.instructions,
                "input": input_messages,
                "max_output_tokens": self.max_output_tokens,
            },
            timeout=self.timeout,
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            detail = ""
            try:
                detail = response.json().get("error", {}).get("message", "")
            except (ValueError, AttributeError):
                detail = response.text[:300]
            raise RuntimeError(f"AI 응답 요청 실패: {detail or exc}") from exc

        answer = extract_output_text(response.json())
        if not answer:
            raise RuntimeError("AI 응답에서 텍스트를 찾지 못했습니다.")

        self.store.append(chat_id, "user", user_text)
        self.store.append(chat_id, "assistant", answer)
        return answer


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip())


def _contains_any(text: str, words: tuple[str, ...]) -> bool:
    return any(word in text for word in words)


def _looks_like_question(text: str) -> bool:
    lowered = text.lower()
    question_words = (
        "어떻게",
        "방법",
        "뭐야",
        "무엇",
        "왜",
        "설명",
        "가능해",
        "할 수 있어",
        "되나",
        "인가",
    )
    explicit_request = (
        "해줘",
        "해주세요",
        "해 주세요",
        "실행해",
        "시작해",
        "만들어줘",
        "생성해줘",
        "올려줘",
        "업로드해줘",
        "예약해줘",
    )
    return ("?" in lowered or _contains_any(lowered, question_words)) and not _contains_any(
        lowered, explicit_request
    )


def _extract_date(text: str) -> Optional[str]:
    lowered = text.lower()
    now = datetime.now(KST)
    if "모레" in lowered:
        return (now.date() + timedelta(days=2)).isoformat()
    if "내일" in lowered:
        return (now.date() + timedelta(days=1)).isoformat()
    if "오늘" in lowered:
        return now.date().isoformat()

    match = re.search(r"(20\d{2})[./-](\d{1,2})[./-](\d{1,2})", text)
    if match:
        year, month, day = map(int, match.groups())
        return datetime(year, month, day).date().isoformat()

    match = re.search(r"(?<!\d)(\d{1,2})\s*월\s*(\d{1,2})\s*일", text)
    if match:
        month, day = map(int, match.groups())
        return datetime(now.year, month, day).date().isoformat()
    return None


def _extract_time(text: str) -> Optional[str]:
    lowered = text.lower()
    match = re.search(r"(?<!\d)(\d{1,2})\s*:\s*(\d{2})(?!\d)", lowered)
    if match:
        hour, minute = map(int, match.groups())
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return f"{hour:02d}:{minute:02d}"

    match = re.search(r"(오전|아침|오후|저녁)?\s*(\d{1,2})\s*시(?:\s*(\d{1,2})\s*분)?", lowered)
    if match:
        period, hour_text, minute_text = match.groups()
        hour = int(hour_text)
        minute = int(minute_text or 0)
        if period in {"오후", "저녁"} and hour < 12:
            hour += 12
        if period in {"오전", "아침"} and hour == 12:
            hour = 0
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return f"{hour:02d}:{minute:02d}"

    if "아침" in lowered:
        return "08:00"
    if "저녁" in lowered:
        return "18:00"
    return None


def _next_date_for_time(time_text: str) -> str:
    now = datetime.now(KST)
    hour, minute = map(int, time_text.split(":"))
    candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if candidate <= now:
        candidate += timedelta(days=1)
    return candidate.date().isoformat()


def _extract_day(text: str) -> Optional[str]:
    patterns = (
        r"(?:day|데이)\s*0*(\d{1,3})",
        r"(?<!\d)0*(\d{1,3})\s*일차",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return str(int(match.group(1))).zfill(3)
    return None


def _extract_jlpt_level(text: str) -> Optional[str]:
    match = re.search(r"(?<![A-Za-z0-9])N\s*([1-5])(?!\d)", text, flags=re.IGNORECASE)
    if match:
        return f"N{match.group(1)}"
    if "비즈니스" in text or "business" in text.lower():
        return "BUSINESS"
    return None


def _extract_topik_level(text: str) -> Optional[str]:
    patterns = (
        r"TOPIK\s*([1-6])",
        r"(?<!\d)([1-6])\s*급",
        r"레벨\s*([1-6])",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return f"TOPIK{match.group(1)}"
    return None


def _is_all_target(text: str, kind: str) -> bool:
    lowered = text.lower()
    if _contains_any(lowered, ("전체", "전부", "모두", "모든", "all_level", "all levels")):
        return True
    if kind == "jlpt" and re.search(r"N\s*1.*N\s*5", text, flags=re.IGNORECASE):
        return True
    if kind == "topik" and (
        re.search(r"1\s*급.*6\s*급", text)
        or re.search(r"TOPIK\s*1.*TOPIK\s*6", text, flags=re.IGNORECASE)
    ):
        return True
    return False


def _control_command(text: str) -> Optional[NaturalCommandResult]:
    lowered = text.lower().strip()
    compact = re.sub(r"\s+", "", lowered)

    if lowered.startswith("/"):
        return NaturalCommandResult()
    if compact in {"시작", "메뉴", "메뉴보여줘", "메뉴열어줘", "메뉴보여주세요"}:
        return NaturalCommandResult(command="/menu")
    if _contains_any(compact, ("상태알려줘", "상태보여줘", "상태확인", "day상태", "진행상태")):
        return NaturalCommandResult(command="/status")
    if compact in {"도움말", "사용법", "명령어", "도움말보여줘"}:
        return NaturalCommandResult(command="/help")
    if "대화" in compact and _contains_any(compact, ("초기화", "기록삭제", "리셋")):
        return NaturalCommandResult(command="/clear_chat")
    return None


def _parse_natural_command(text: str, kind: str) -> NaturalCommandResult:
    text = _normalize_text(text)
    if not text:
        return NaturalCommandResult(command="/menu")

    control = _control_command(text)
    if control is not None:
        return control

    if _looks_like_question(text):
        return NaturalCommandResult()

    lowered = text.lower()
    level = _extract_jlpt_level(text) if kind == "jlpt" else _extract_topik_level(text)
    all_target = _is_all_target(text, kind)
    day = _extract_day(text)
    date_text = _extract_date(text)
    time_text = _extract_time(text)

    upload_requested = _contains_any(lowered, ("업로드", "올려줘", "올려 주세요", "예약", "게시"))
    finalize_requested = kind == "jlpt" and _contains_any(lowered, ("백업", "정리", "finalize"))
    generate_requested = _contains_any(lowered, ("생성", "만들", "제작", "뽑아", "실행"))

    if upload_requested:
        if time_text and not date_text:
            date_text = _next_date_for_time(time_text)

        if all_target:
            if date_text and not time_text:
                return NaturalCommandResult(message="예약 업로드 시간을 함께 말해 주세요. 예: `2026-07-02 오후 6시에 전체 업로드해줘`")
            if date_text and time_text:
                if time_text == "08:00":
                    return NaturalCommandResult(command=f"/2 {date_text}")
                if time_text == "18:00":
                    return NaturalCommandResult(command=f"/3 {date_text}")
                return NaturalCommandResult(command=f"/upload_at all_level {date_text} {time_text}")
            return NaturalCommandResult(command="/upload all_level")

        if level:
            if not day:
                if _contains_any(lowered, ("최신", "최근", "방금", "마지막")):
                    return NaturalCommandResult(command=f"/upload_latest {level}")
                return NaturalCommandResult(
                    message=f"{level} 업로드에는 DAY 번호가 필요합니다. 예: `{level} DAY 12 영상을 업로드해줘`"
                )
            if date_text and not time_text:
                return NaturalCommandResult(message="예약 업로드 시간을 함께 말해 주세요. 예: `오후 6시`")
            if date_text and time_text:
                return NaturalCommandResult(command=f"/upload_at {level} {day} {date_text} {time_text}")
            return NaturalCommandResult(command=f"/upload {level} {day}")

        return NaturalCommandResult(message="업로드 대상을 말해 주세요. 예: `전체 최신본 업로드해줘` 또는 `N3 DAY 12 업로드해줘`")

    if finalize_requested:
        if level and day:
            return NaturalCommandResult(command=f"/finalize {level} {day}")
        return NaturalCommandResult(message="정리할 레벨과 DAY를 말해 주세요. 예: `N5 DAY 45 백업 정리해줘`")

    if generate_requested:
        if all_target:
            return NaturalCommandResult(command="/make all_level")
        if level:
            if kind == "jlpt" and level == "BUSINESS":
                return NaturalCommandResult(command="/business")
            return NaturalCommandResult(command=f"/make {level}")
        target_hint = "N1~N5 또는 BUSINESS" if kind == "jlpt" else "TOPIK 1급~6급"
        return NaturalCommandResult(message=f"생성할 레벨을 말해 주세요. 예: `{target_hint} 중 하나를 만들어줘`")

    return NaturalCommandResult()


def parse_jlpt_natural_command(text: str) -> NaturalCommandResult:
    return _parse_natural_command(text, "jlpt")


def parse_topik_natural_command(text: str) -> NaturalCommandResult:
    return _parse_natural_command(text, "topik")
