import io
import json
import traceback
from pathlib import Path
from contextlib import redirect_stdout
from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st

import main
from src.data.day_manager import get_current_day_number
from src.drive.google_drive_uploader import backup_compilation_assets
from src.youtube.youtube_uploader import (
    build_publish_at_from_kst,
    fetch_video_schedule_by_level_day,
    update_video_schedule_by_level_day,
)
from src.video.level_compilation_generator import create_level_compilation
from src.youtube.compilation_uploader import (
    build_compilation_thumbnail_path,
    build_compilation_title,
    build_compilation_video_path,
    upload_compilation_video,
)


LEVEL_OPTIONS = ["N1", "N2", "N3", "N4", "N5", "BUSINESS"]
ACTION_OPTIONS = ["전체 실행", "생성만", "업로드만"]
UPLOAD_LOG_PATH = Path("data/uploaded_log.json")
RUN_LOG_PATH = Path("data/streamlit_run_log.json")
JLPT_LEVELS = ["N1", "N2", "N3", "N4", "N5"]
BUSINESS_LEVELS = ["BUSINESS"]
DAY_VIDEO_ROOT = Path("output/day_videos")
THUMBNAIL_ROOT = Path("output/thumbnails")
COMPILATION_LEVELS = ["N1", "N2", "N3", "N4", "N5"]
COMPILATION_UNIT = 25
PREFLIGHT_REQUIRED_FILES = [
    ("client_secret.json", "Google API 클라이언트 시크릿"),
    ("data/words.json", "현재 작업 words.json"),
    ("data/day_status.json", "DAY 상태 파일"),
    ("assets/fonts/NotoSansJP-Bold.ttf", "일본어 폰트"),
    ("assets/fonts/NotoSansKR-Bold.ttf", "한국어 폰트"),
    ("assets/backgrounds/default.jpg", "기본 배경 이미지"),
]


class LiveLogWriter:
    def __init__(self, placeholder):
        self.placeholder = placeholder
        self.buffer = io.StringIO()

    def write(self, text):
        self.buffer.write(text)
        current = self.buffer.getvalue().strip()
        self.placeholder.code(current or "로그 대기 중...", language="text")
        return len(text)

    def flush(self):
        return None

    def getvalue(self):
        return self.buffer.getvalue()


def normalize_day_input(day_text):
    value = str(day_text).strip()
    if not value:
        return None

    value = value.upper().replace("DAY", "").replace("_", "").replace("-", "").strip()
    if not value.isdigit():
        raise ValueError("업로드 DAY는 숫자 또는 DAY001 형식으로 입력해 주세요.")

    return value.zfill(3)


def get_generated_days(level):
    level_dir = DAY_VIDEO_ROOT / level
    if not level_dir.exists():
        return []

    prefix = f"{level}_DAY_"
    days = []

    for file_path in sorted(level_dir.glob(f"{level}_DAY_*.mp4")):
        stem = file_path.stem
        if not stem.startswith(prefix):
            continue

        day = stem.replace(prefix, "", 1).strip()
        if day.isdigit():
            days.append(day.zfill(3))

    return sorted(set(days), reverse=True)


def get_upload_preview_rows(upload_day_map):
    log_data = load_uploaded_log()
    preview_rows = []

    for level, day in upload_day_map.items():
        video_path = DAY_VIDEO_ROOT / level / f"{level}_DAY_{day}.mp4"
        thumbnail_path = THUMBNAIL_ROOT / f"{level}_DAY_{day}.jpg"
        upload_key = f"{level}_DAY_{day}"

        log_entry = log_data.get(upload_key, {})
        if not isinstance(log_entry, dict):
            log_entry = {"uploaded": bool(log_entry)}

        preview_rows.append({
            "레벨": level,
            "DAY": f"DAY {day}",
            "영상 파일": "있음" if video_path.exists() else "없음",
            "썸네일 파일": "있음" if thumbnail_path.exists() else "없음",
            "이미 업로드됨": "예" if log_entry.get("uploaded") else "아니오",
            "예약 시간": format_publish_at_kst(log_entry.get("publish_at")),
            "영상 경로": str(video_path),
            "썸네일 경로": str(thumbnail_path),
        })

    return preview_rows


def get_uploaded_video_options():
    options = []
    for upload_key, entry in load_uploaded_log().items():
        if isinstance(entry, dict):
            uploaded = entry.get("uploaded", True)
            video_id = entry.get("video_id")
        else:
            uploaded = bool(entry)
            video_id = None

        if not uploaded:
            continue

        level, day = upload_key.split("_DAY_") if "_DAY_" in upload_key else ("기타", "---")
        options.append({
            "upload_key": upload_key,
            "level": level,
            "day": day,
            "video_id": video_id,
            "publish_at": entry.get("publish_at") if isinstance(entry, dict) else None,
            "publish_at_kst": format_publish_at_kst(entry.get("publish_at") if isinstance(entry, dict) else None),
        })

    return sorted(options, key=lambda item: (item["level"], item["day"]), reverse=True)


def format_publish_at_kst(publish_at):
    if not publish_at:
        return "기록 없음"

    try:
        dt = datetime.fromisoformat(str(publish_at).replace("Z", "+00:00"))
        kst = dt.astimezone(ZoneInfo("Asia/Seoul"))
        return kst.strftime("%Y-%m-%d %H:%M:%S KST")
    except Exception:
        return str(publish_at)


def run_compilation_task(
    levels,
    action_mode,
    start_day,
    end_day,
    privacy_status,
    publish_at,
    log_placeholder,
    status_placeholder,
    progress_bar,
):
    writer = LiveLogWriter(log_placeholder)
    total_levels = max(len(levels), 1)

    with redirect_stdout(writer):
        for index, level in enumerate(levels, start=1):
            progress_bar.progress((index - 1) / total_levels, text=f"{level} 풀영상 작업 준비 중")
            status_placeholder.info(f"{level} 풀영상 처리 중 ({index}/{total_levels})")

            if action_mode == "생성만":
                create_level_compilation(level=level, start_day=start_day, end_day=end_day)
            elif action_mode == "업로드만":
                upload_compilation_video(
                    level=level,
                    start_day=start_day,
                    end_day=end_day,
                    privacy_status=privacy_status,
                    publish_at=publish_at,
                )
                print("풀영상 Google Drive 자동 백업 및 로컬 정리를 시작합니다.")
                backup_compilation_assets(
                    level=level,
                    start_day=start_day,
                    end_day=end_day,
                    delete_local=True,
                )
            else:
                create_level_compilation(level=level, start_day=start_day, end_day=end_day)
                upload_compilation_video(
                    level=level,
                    start_day=start_day,
                    end_day=end_day,
                    privacy_status=privacy_status,
                    publish_at=publish_at,
                )
                print("풀영상 Google Drive 자동 백업 및 로컬 정리를 시작합니다.")
                backup_compilation_assets(
                    level=level,
                    start_day=start_day,
                    end_day=end_day,
                    delete_local=True,
                )

            progress_bar.progress(index / total_levels, text=f"{level} 풀영상 완료")

    status_placeholder.success("선택한 풀영상 작업이 모두 완료되었습니다.")
    return writer.getvalue()


def run_compilation_drive_backup_task(
    levels,
    start_day,
    end_day,
    delete_local,
    log_placeholder,
    status_placeholder,
    progress_bar,
):
    writer = LiveLogWriter(log_placeholder)
    total_levels = max(len(levels), 1)

    with redirect_stdout(writer):
        for index, level in enumerate(levels, start=1):
            progress_bar.progress((index - 1) / total_levels, text=f"{level} 풀영상 Drive 백업 준비 중")
            status_placeholder.info(
                f"{level} DAY {int(start_day):03d}~{int(end_day):03d} 풀영상 Drive 백업 중 ({index}/{total_levels})"
            )
            result = backup_compilation_assets(
                level=level,
                start_day=start_day,
                end_day=end_day,
                delete_local=delete_local,
            )
            print("풀영상 Drive 백업 완료:", result["upload_key"])

            if delete_local:
                print("풀영상 로컬 삭제 완료:", result["deleted_files"])

            progress_bar.progress(index / total_levels, text=f"{level} 풀영상 Drive 백업 완료")

    status_placeholder.success("선택한 풀영상 Drive 백업 작업이 모두 완료되었습니다.")
    return writer.getvalue()


def get_compilation_preview_rows(levels, start_day, end_day):
    rows = []
    log_data = load_uploaded_log()
    for level in levels:
        video_path = Path(build_compilation_video_path(level, start_day, end_day))
        thumbnail_path = Path(build_compilation_thumbnail_path(level, start_day, end_day))
        upload_key = f"{level}_DAY_{int(start_day):03d}_{int(end_day):03d}_FULL"
        log_entry = log_data.get(upload_key, {})
        if not isinstance(log_entry, dict):
            log_entry = {"uploaded": bool(log_entry)}
        rows.append({
            "레벨": level,
            "범위": f"DAY {start_day:03d} ~ DAY {end_day:03d}",
            "영상 파일": "있음" if video_path.exists() else "없음",
            "썸네일 파일": "있음" if thumbnail_path.exists() else "없음",
            "Drive 백업됨": "예" if log_entry.get("drive_backed_up") else "아니오",
            "Drive 영상 링크": log_entry.get("drive_video_link") or "-",
            "Drive 썸네일 링크": log_entry.get("drive_thumbnail_link") or "-",
            "영상 경로": str(video_path),
            "썸네일 경로": str(thumbnail_path),
            "제목": build_compilation_title(level, start_day, end_day),
        })

    return rows


def run_selected_levels(
    levels,
    action_mode,
    upload_day_map,
    privacy_status,
    publish_at,
    log_placeholder,
    status_placeholder,
    progress_bar,
):
    original_auto_upload = main.AUTO_UPLOAD
    writer = LiveLogWriter(log_placeholder)
    total_levels = max(len(levels), 1)

    try:
        with redirect_stdout(writer):
            for index, level in enumerate(levels, start=1):
                print("=" * 60)
                print("RUN LEVEL:", level)
                target_day = upload_day_map.get(level) or main.get_latest_generated_day(level)
                progress_bar.progress((index - 1) / total_levels, text=f"{level} 작업 준비 중")
                status_placeholder.info(f"{level} 처리 중 ({index}/{total_levels})")

                try:
                    if action_mode == "전체 실행":
                        main.AUTO_UPLOAD = True
                        main.run_pipeline(level, privacy_status=privacy_status, publish_at=publish_at)
                        append_run_log("success", level, action_mode, None, "전체 실행 완료")
                    elif action_mode == "생성만":
                        main.AUTO_UPLOAD = False
                        created_day = main.generate_pipeline(level)
                        print("생성 완료 DAY:", created_day)
                        append_run_log("success", level, action_mode, created_day, "생성 완료")
                    else:
                        print("업로드 대상 DAY:", target_day)
                        main.upload_existing_day(
                            level,
                            target_day,
                            privacy_status=privacy_status,
                            publish_at=publish_at,
                        )
                        print("Google Drive 자동 백업 및 로컬 정리를 시작합니다.")
                        main.finalize_uploaded_day(
                            level,
                            target_day,
                            delete_local=True,
                            cleanup_intermediate=True,
                        )
                        append_run_log("success", level, action_mode, target_day, "업로드 완료")

                    progress_bar.progress(index / total_levels, text=f"{level} 완료")
                except Exception as error:
                    error_message = str(error).strip() or error.__class__.__name__
                    append_run_log(
                        "failed",
                        level,
                        action_mode,
                        target_day if action_mode == "업로드만" else None,
                        error_message,
                        traceback.format_exc(),
                    )
                    print("ERROR:", error_message)
                    progress_bar.progress(index / total_levels, text=f"{level} 실패")
                    status_placeholder.error(f"{level} 처리 중 오류가 발생했습니다.")
                    raise

    finally:
        main.AUTO_UPLOAD = original_auto_upload

    status_placeholder.success("선택한 작업이 모두 완료되었습니다.")
    return writer.getvalue()


def load_uploaded_log():
    if not UPLOAD_LOG_PATH.exists():
        return {}

    with UPLOAD_LOG_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_run_log():
    if not RUN_LOG_PATH.exists():
        return []

    with RUN_LOG_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, list):
        return data

    return []


def save_run_log(entries):
    with RUN_LOG_PATH.open("w", encoding="utf-8") as file:
        json.dump(entries, file, ensure_ascii=False, indent=2)


def append_run_log(status, level, action_mode, day, message, trace_text=None):
    entries = load_run_log()
    entries.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": status,
        "level": level,
        "action_mode": action_mode,
        "day": day,
        "message": message,
        "traceback": trace_text,
    })
    save_run_log(entries[-200:])


def parse_upload_key(upload_key):
    parts = upload_key.split("_DAY_")
    if len(parts) != 2:
        return {"key": upload_key, "level": "기타", "day": "-", "sort_day": -1}

    level, day = parts
    try:
        sort_day = int(day)
    except ValueError:
        sort_day = -1

    return {
        "key": upload_key,
        "level": level,
        "day": f"DAY {day}",
        "sort_day": sort_day,
    }


def build_upload_summary():
    log_data = load_uploaded_log()
    level_counts = {level: 0 for level in LEVEL_OPTIONS}
    parsed_rows = []

    for upload_key, uploaded in log_data.items():
        if isinstance(uploaded, dict):
            is_done = uploaded.get("uploaded", True)
        else:
            is_done = bool(uploaded)

        if not is_done:
            continue

        row = parse_upload_key(upload_key)
        if isinstance(uploaded, dict):
            row["publish_at"] = uploaded.get("publish_at")
            row["video_id"] = uploaded.get("video_id")
        parsed_rows.append(row)

        if row["level"] in level_counts:
            level_counts[row["level"]] += 1

    summary_rows = []
    for level in LEVEL_OPTIONS:
        latest_day = max(
            (row["sort_day"] for row in parsed_rows if row["level"] == level),
            default=0,
        )
        summary_rows.append({
            "레벨": level,
            "업로드 수": level_counts[level],
            "최근 업로드": f"DAY {latest_day:03d}" if latest_day > 0 else "-",
        })

    recent_rows = sorted(
        parsed_rows,
        key=lambda row: (row["sort_day"], row["level"]),
        reverse=True,
    )[:20]

    return summary_rows, recent_rows, log_data


def build_run_log_summary():
    entries = list(reversed(load_run_log()))
    failed_rows = [entry for entry in entries if entry.get("status") == "failed"]
    success_rows = [entry for entry in entries if entry.get("status") == "success"]

    summary = {
        "총 실행 기록": len(entries),
        "성공": len(success_rows),
        "실패": len(failed_rows),
    }

    recent_failures = failed_rows[:20]
    recent_runs = entries[:20]

    return summary, recent_failures, recent_runs


def get_latest_uploaded_schedule_for_level(level):
    level_text = str(level).strip().upper()
    latest_entry = None
    latest_day = -1

    for upload_key, entry in load_uploaded_log().items():
        if "_DAY_" not in upload_key:
            continue

        key_level, key_day = upload_key.split("_DAY_", 1)
        if key_level != level_text:
            continue

        day_digits = "".join(ch for ch in key_day if ch.isdigit())
        if not day_digits:
            continue

        day_number = int(day_digits)
        current_entry = entry if isinstance(entry, dict) else {"uploaded": bool(entry)}
        if not current_entry.get("uploaded", True):
            continue

        if day_number > latest_day:
            latest_day = day_number
            latest_entry = {
                "upload_key": upload_key,
                "day": f"DAY {day_digits.zfill(3)}",
                "publish_at": current_entry.get("publish_at"),
            }

    return latest_entry


def get_available_compilation_ranges(levels, unit=COMPILATION_UNIT):
    if not levels:
        return []

    completed_days = [
        max(get_current_day_number(level) - 1, 0)
        for level in levels
    ]
    max_common_completed_day = min(completed_days) if completed_days else 0
    full_range_count = max_common_completed_day // unit

    ranges = []
    for index in range(full_range_count):
        start_day = index * unit + 1
        end_day = start_day + unit - 1
        ranges.append({
            "label": f"DAY {start_day:03d} ~ DAY {end_day:03d}",
            "start_day": start_day,
            "end_day": end_day,
        })

    return ranges


def build_compilation_availability_rows(levels):
    rows = []

    for level in levels:
        completed_day = max(get_current_day_number(level) - 1, 0)
        available_range_count = completed_day // COMPILATION_UNIT

        if completed_day < COMPILATION_UNIT:
            reason = f"아직 풀영상 제작 기준인 {COMPILATION_UNIT}일치 DAY가 쌓이지 않았습니다."
        else:
            reason = f"{available_range_count}개 구간 선택 가능"

        rows.append({
            "레벨": level,
            "완료 DAY": f"DAY {completed_day:03d}" if completed_day > 0 else "-",
            "상태": "가능" if completed_day >= COMPILATION_UNIT else "부족",
            "사유": reason,
        })

    return rows


def build_preflight_rows():
    rows = []

    for relative_path, label in PREFLIGHT_REQUIRED_FILES:
        path = Path(relative_path)
        rows.append({
            "항목": label,
            "경로": str(path),
            "상태": "정상" if path.exists() else "없음",
        })

    token_path = Path("token.json")
    drive_token_path = Path("drive_token.json")

    rows.append({
        "항목": "YouTube 인증 토큰",
        "경로": str(token_path),
        "상태": "있음" if token_path.exists() else "없음",
    })
    rows.append({
        "항목": "Google Drive 인증 토큰",
        "경로": str(drive_token_path),
        "상태": "있음" if drive_token_path.exists() else "없음",
    })

    return rows


st.set_page_config(
    page_title="JLPT / 비즈니스 쇼츠 대시보드",
    page_icon="🎬",
    layout="wide",
)

st.title("JLPT / 비즈니스 쇼츠 대시보드")
st.caption("쇼츠 생성 및 업로드 제어 화면")

with st.sidebar:
    st.header("실행 모니터")
    st.caption("작업 진행 상황과 로그를 여기에서 바로 확인합니다.")

    st.subheader("쇼츠 실행 상태")
    status_placeholder = st.empty()
    progress_bar = st.progress(0, text="대기 중")
    live_log_placeholder = st.empty()
    live_log_placeholder.code("로그 대기 중...", language="text")

    st.divider()

    st.subheader("풀영상 실행 상태")
    comp_status_placeholder = st.empty()
    comp_progress_bar = st.progress(0, text="대기 중")
    comp_live_log_placeholder = st.empty()
    comp_live_log_placeholder.code("풀영상 로그 대기 중...", language="text")

st.subheader("사전 점검")
preflight_button = st.button("사전 점검 실행", use_container_width=True)

if preflight_button:
    preflight_rows = build_preflight_rows()
    st.dataframe(preflight_rows, use_container_width=True, hide_index=True)

    missing_rows = [row for row in preflight_rows if row["상태"] in {"없음"}]
    if missing_rows:
        st.warning("일부 필수 항목이 준비되지 않았습니다. 실행 전에 확인해 주세요.")
    else:
        st.success("기본 필수 항목 점검이 완료되었습니다.")

st.subheader("빠른 실행")

quick_col1, quick_col2, quick_col3 = st.columns([1, 1, 1])

if "preset_levels" not in st.session_state:
    st.session_state.preset_levels = ["BUSINESS"]
if "preset_action_mode" not in st.session_state:
    st.session_state.preset_action_mode = "생성만"
if "preset_upload_day_text" not in st.session_state:
    st.session_state.preset_upload_day_text = ""
if "selected_levels" not in st.session_state:
    st.session_state.selected_levels = st.session_state.preset_levels
if "action_mode" not in st.session_state:
    st.session_state.action_mode = st.session_state.preset_action_mode
if "upload_day_text" not in st.session_state:
    st.session_state.upload_day_text = st.session_state.preset_upload_day_text

with quick_col1:
    if st.button("BUSINESS만 생성", use_container_width=True):
        st.session_state.preset_levels = BUSINESS_LEVELS
        st.session_state.preset_action_mode = "생성만"
        st.session_state.preset_upload_day_text = ""
        st.session_state.selected_levels = BUSINESS_LEVELS
        st.session_state.action_mode = "생성만"
        st.session_state.upload_day_text = ""

with quick_col2:
    if st.button("JLPT 전체 생성", use_container_width=True):
        st.session_state.preset_levels = JLPT_LEVELS
        st.session_state.preset_action_mode = "생성만"
        st.session_state.preset_upload_day_text = ""
        st.session_state.selected_levels = JLPT_LEVELS
        st.session_state.action_mode = "생성만"
        st.session_state.upload_day_text = ""

with quick_col3:
    if st.button("선택 레벨 업로드만", use_container_width=True):
        st.session_state.preset_action_mode = "업로드만"
        st.session_state.action_mode = "업로드만"

left, right = st.columns([1, 1])

with left:
    st.subheader("파이프라인 실행")

    selected_levels = st.multiselect(
        "실행할 레벨 선택",
        LEVEL_OPTIONS,
        key="selected_levels",
    )

    action_mode = st.radio(
        "실행 모드",
        ACTION_OPTIONS,
        horizontal=True,
        key="action_mode",
    )

    privacy_status = "private"
    publish_at = None
    if action_mode in {"전체 실행", "업로드만"}:
        upload_mode = st.radio(
            "업로드 공개 방식",
            ["비공개", "즉시 공개", "예약 공개"],
            horizontal=True,
            key="upload_visibility_mode",
        )

        if upload_mode == "비공개":
            privacy_status = "private"
        elif upload_mode == "즉시 공개":
            privacy_status = "public"
        else:
            privacy_status = "private"
            schedule_date = st.date_input("예약 날짜", key="schedule_date")
            schedule_time = st.time_input("예약 시간", key="schedule_time")
            publish_at = build_publish_at_from_kst(schedule_date, schedule_time)
            st.caption("입력한 날짜와 시간은 한국 시간(KST) 기준으로 예약됩니다.")

        st.caption(
            "업로드가 성공하면 Google Drive에 자동 백업한 뒤, "
            "DAY 영상/썸네일을 자동 삭제합니다. "
            "신규 생성분은 중간 산출물도 함께 정리됩니다."
        )

        if selected_levels:
            latest_schedule_rows = []
            for level in selected_levels:
                latest_entry = get_latest_uploaded_schedule_for_level(level)
                latest_schedule_rows.append({
                    "레벨": level,
                    "가장 최근 업로드": latest_entry["day"] if latest_entry else "-",
                    "최근 예약 시간": (
                        format_publish_at_kst(latest_entry.get("publish_at"))
                        if latest_entry
                        else "기록 없음"
                    ),
                })

            st.subheader("선택 레벨 최근 예약 정보")
            st.dataframe(latest_schedule_rows, use_container_width=True, hide_index=True)

    upload_day_map = {}
    upload_preview_rows = []
    if action_mode == "업로드만":
        st.caption("실제로 생성된 DAY 목록에서 업로드할 영상을 직접 선택합니다.")

        for level in selected_levels:
            generated_days = get_generated_days(level)
            select_key = f"upload_day_select_{level}"

            if generated_days:
                if select_key not in st.session_state or st.session_state[select_key] not in generated_days:
                    st.session_state[select_key] = generated_days[0]

                upload_day_map[level] = st.selectbox(
                    f"{level} 업로드 DAY 선택",
                    options=generated_days,
                    key=select_key,
                    format_func=lambda day: f"DAY {day}",
                )
            else:
                st.warning(f"{level}은 아직 생성된 DAY 영상이 없습니다.")

        if upload_day_map:
            st.subheader("업로드 전 확인")
            upload_preview_rows = get_upload_preview_rows(upload_day_map)
            st.dataframe(upload_preview_rows, use_container_width=True, hide_index=True)

            missing_assets = [
                row for row in upload_preview_rows
                if row["영상 파일"] == "없음" or row["썸네일 파일"] == "없음"
            ]
            already_uploaded = [
                row for row in upload_preview_rows
                if row["이미 업로드됨"] == "예"
            ]

            if missing_assets:
                st.error("일부 선택 항목에 영상 또는 썸네일 파일이 없습니다. 실행 전에 확인해 주세요.")

            if already_uploaded:
                st.warning("이미 업로드된 항목이 포함되어 있습니다. 중복 업로드를 피하려면 선택을 다시 확인해 주세요.")

    run_button = st.button(
        "실행 시작",
        type="primary",
        use_container_width=True,
    )

with right:
    st.subheader("현재 DAY 상태")

    status_rows = []
    for level in LEVEL_OPTIONS:
        next_day = get_current_day_number(level)
        current_day = max(next_day - 1, 0)
        status_rows.append({
            "레벨": level,
            "현재 DAY": f"DAY {current_day:03d}" if current_day > 0 else "-",
            "다음 DAY": f"DAY {next_day:03d}",
        })

    st.dataframe(status_rows, use_container_width=True, hide_index=True)

st.divider()

log_left, log_right = st.columns([1, 1])

with log_left:
    st.subheader("업로드 현황")
    summary_rows, recent_rows, raw_log_data = build_upload_summary()
    st.dataframe(summary_rows, use_container_width=True, hide_index=True)

with log_right:
    st.subheader("최근 업로드 20개")
    if recent_rows:
        display_rows = [
            {
                "레벨": row["level"],
                "DAY": row["day"],
                "로그 키": row["key"],
                "예약 시간": format_publish_at_kst(row.get("publish_at")),
            }
            for row in recent_rows
        ]
        st.dataframe(display_rows, use_container_width=True, hide_index=True)
    else:
        st.info("업로드 기록이 아직 없습니다.")

with st.expander("업로드 로그 JSON 보기"):
    st.json(raw_log_data)

st.divider()

st.subheader("기존 업로드 예약 변경")

with st.expander("YouTube 재인증 안내"):
    st.markdown(
        """
1. `F:\\jlpt_word\\token.json` 파일을 삭제합니다.
2. 이 화면에서 업로드 또는 `유튜브 실제 예약 불러오기`를 다시 실행합니다.
3. 구글 로그인 창이 뜨면 유튜브 채널 계정으로 다시 인증합니다.
4. 새 `token.json`이 생성되면 예약 조회와 예약 변경을 다시 사용할 수 있습니다.
"""
    )

refresh_schedule_button = st.button("유튜브 실제 예약 불러오기", use_container_width=True)

if refresh_schedule_button:
    with st.spinner("유튜브에서 실제 예약 시간을 불러오는 중입니다."):
        refresh_errors = []
        auth_error = None
        for item in get_uploaded_video_options():
            try:
                fetch_video_schedule_by_level_day(item["level"], item["day"])
            except Exception as error:
                error_text = str(error)
                if "YouTube 인증이 만료되었거나 해제되었습니다" in error_text:
                    auth_error = error_text
                    break
                refresh_errors.append(f"{item['upload_key']}: {error}")

        if auth_error:
            st.error(auth_error)
            st.info(
                "`token.json`을 지우고 다시 업로드/예약 조회를 실행해서 "
                "구글 로그인 인증을 다시 진행해 주세요."
            )
        elif refresh_errors:
            st.warning("일부 항목은 실제 예약 시간을 불러오지 못했습니다.")
            with st.expander("예약 불러오기 실패 항목"):
                for message in refresh_errors:
                    st.write(message)
        else:
            st.success("유튜브의 실제 예약 시간을 모두 새로 불러왔습니다.")

uploaded_video_options = get_uploaded_video_options()

if uploaded_video_options:
    st.dataframe(
        [
            {
                "레벨": item["level"],
                "DAY": f"DAY {item['day']}",
                "현재 예약 시간": item["publish_at_kst"],
                "VIDEO ID": item.get("video_id") or "미기록",
            }
            for item in uploaded_video_options
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.caption("예약 시간이 있는 항목을 먼저 확인한 뒤, 아래에서 변경할 영상을 선택하세요.")

    reschedule_levels = sorted({item["level"] for item in uploaded_video_options})
    selected_reschedule_level = st.selectbox(
        "예약 변경 레벨 선택",
        options=reschedule_levels,
        key="reschedule_level",
    )

    filtered_reschedule_options = [
        item for item in uploaded_video_options
        if item["level"] == selected_reschedule_level
    ]

    selected_reschedule_day_label = st.selectbox(
        "예약 변경 DAY 선택",
        options=[f"DAY {item['day']}" for item in filtered_reschedule_options],
        key="reschedule_day",
    )

    selected_reschedule = next(
        item
        for item in filtered_reschedule_options
        if f"DAY {item['day']}" == selected_reschedule_day_label
    )

    st.write(
        f"현재 선택: `{selected_reschedule['upload_key']}` / VIDEO ID: `{selected_reschedule.get('video_id') or '미기록'}`"
    )

    info_col1, info_col2, info_col3 = st.columns([1, 1, 1])
    with info_col1:
        st.metric("선택 레벨", selected_reschedule["level"])
    with info_col2:
        st.metric("선택 DAY", f"DAY {selected_reschedule['day']}")
    with info_col3:
        st.metric("현재 예약 시간", format_publish_at_kst(selected_reschedule.get("publish_at")))

    reschedule_date = st.date_input("변경할 예약 날짜", key="reschedule_date")
    reschedule_time = st.time_input("변경할 예약 시간", key="reschedule_time")
    reschedule_button = st.button("예약 날짜 변경", use_container_width=True)

    if reschedule_button:
        try:
            new_publish_at = build_publish_at_from_kst(reschedule_date, reschedule_time)
            video_id = update_video_schedule_by_level_day(
                level=selected_reschedule["level"],
                day=selected_reschedule["day"],
                privacy_status="private",
                publish_at=new_publish_at,
            )
            append_run_log(
                "success",
                selected_reschedule["level"],
                "예약 변경",
                selected_reschedule["day"],
                f"예약 시간 변경 완료 ({new_publish_at}) / VIDEO ID {video_id}",
            )
            st.success("예약 날짜와 시간이 변경되었습니다.")
        except Exception as error:
            append_run_log(
                "failed",
                selected_reschedule["level"],
                "예약 변경",
                selected_reschedule["day"],
                str(error).strip() or error.__class__.__name__,
                traceback.format_exc(),
            )
            st.error(f"예약 변경 중 오류가 발생했습니다: {error}")
else:
    st.info("예약 변경 가능한 업로드 기록이 아직 없습니다.")

st.divider()

run_left, run_right = st.columns([1, 1])

run_summary, recent_failures, recent_runs = build_run_log_summary()

with run_left:
    st.subheader("실행 기록 요약")
    st.metric("총 실행 기록", run_summary["총 실행 기록"])
    st.metric("성공", run_summary["성공"])
    st.metric("실패", run_summary["실패"])

with run_right:
    st.subheader("최근 실패 20개")
    if recent_failures:
        failure_rows = [
            {
                "시각": row["timestamp"],
                "레벨": row["level"],
                "모드": row["action_mode"],
                "DAY": row["day"] or "-",
                "오류": row["message"],
            }
            for row in recent_failures
        ]
        st.dataframe(failure_rows, use_container_width=True, hide_index=True)
    else:
        st.info("기록된 실패 내역이 없습니다.")

with st.expander("최근 실행 20개 보기"):
    if recent_runs:
        run_rows = [
            {
                "시각": row["timestamp"],
                "상태": "성공" if row["status"] == "success" else "실패",
                "레벨": row["level"],
                "모드": row["action_mode"],
                "DAY": row["day"] or "-",
                "메시지": row["message"],
            }
            for row in recent_runs
        ]
        st.dataframe(run_rows, use_container_width=True, hide_index=True)
    else:
        st.info("실행 기록이 아직 없습니다.")

with st.expander("최근 실패 Traceback 보기"):
    if recent_failures:
        latest_failure = recent_failures[0]
        st.write(
            f"최근 실패: {latest_failure['timestamp']} / {latest_failure['level']} / {latest_failure['action_mode']}"
        )
        st.code(latest_failure.get("traceback") or latest_failure["message"], language="text")
    else:
        st.info("표시할 실패 Traceback이 없습니다.")

if run_button:
    if not selected_levels:
        st.warning("최소 한 개 이상의 레벨을 선택해 주세요.")
    elif action_mode == "업로드만" and not upload_day_map:
        st.warning("업로드할 생성 완료 영상이 없습니다.")
    elif action_mode == "업로드만" and any(
        row["영상 파일"] == "없음" or row["썸네일 파일"] == "없음"
        for row in upload_preview_rows
    ):
        st.error("영상 또는 썸네일 파일이 없는 항목이 있어 업로드를 시작하지 않았습니다.")
    else:
        try:
            with st.spinner("작업 실행 중입니다. 시간이 조금 걸릴 수 있습니다."):
                logs = run_selected_levels(
                    selected_levels,
                    action_mode,
                    upload_day_map,
                    privacy_status,
                    publish_at,
                    live_log_placeholder,
                    status_placeholder,
                    progress_bar,
                )
        except ValueError as error:
            st.error(str(error))
            status_placeholder.error("입력값을 확인해 주세요.")
        else:
            st.success("작업이 완료되었습니다.")
            st.subheader("실행 로그")
            st.code(logs or "기록된 로그가 없습니다.", language="text")

else:
    st.info("레벨과 실행 모드를 선택한 뒤 '실행 시작' 버튼을 눌러 주세요.")

st.divider()
st.header("풀영상 관리")

comp_left, comp_right = st.columns([1, 1])

with comp_left:
    compilation_levels = st.multiselect(
        "풀영상 레벨 선택",
        COMPILATION_LEVELS,
        default=["N1"],
        key="compilation_levels",
    )
    compilation_action_mode = st.radio(
        "풀영상 실행 모드",
        ["생성만", "업로드만", "생성 후 업로드"],
        horizontal=True,
        key="compilation_action_mode",
    )

    compilation_range_options = get_available_compilation_ranges(compilation_levels)
    compilation_availability_rows = build_compilation_availability_rows(compilation_levels)
    compilation_start_day = 1
    compilation_end_day = COMPILATION_UNIT

    if compilation_levels:
        st.dataframe(compilation_availability_rows, use_container_width=True, hide_index=True)

    if compilation_range_options:
        selected_compilation_range_label = st.selectbox(
            "풀영상 구간 선택",
            options=[item["label"] for item in compilation_range_options],
            key="compilation_range_label",
        )
        selected_compilation_range = next(
            item
            for item in compilation_range_options
            if item["label"] == selected_compilation_range_label
        )
        compilation_start_day = selected_compilation_range["start_day"]
        compilation_end_day = selected_compilation_range["end_day"]
        st.caption("완료 이력 기준으로 선택 가능한 25일 단위 구간만 표시합니다.")
    else:
        if compilation_levels:
            st.warning("선택한 레벨 기준으로 아직 완성된 25일 단위 풀영상 구간이 없습니다.")
            st.info("보통 각 레벨이 최소 DAY 025까지 완료되어야 첫 번째 풀영상 구간이 열립니다.")
        else:
            st.info("먼저 풀영상 레벨을 선택해 주세요.")

    compilation_privacy_status = "private"
    compilation_publish_at = None
    if compilation_action_mode in {"업로드만", "생성 후 업로드"}:
        compilation_upload_mode = st.radio(
            "풀영상 업로드 공개 방식",
            ["비공개", "즉시 공개", "예약 공개"],
            horizontal=True,
            key="compilation_upload_mode",
        )
        if compilation_upload_mode == "즉시 공개":
            compilation_privacy_status = "public"
        else:
            compilation_privacy_status = "private"

        if compilation_upload_mode == "예약 공개":
            compilation_schedule_date = st.date_input("풀영상 예약 날짜", key="compilation_schedule_date")
            compilation_schedule_time = st.time_input("풀영상 예약 시간", key="compilation_schedule_time")
            compilation_publish_at = build_publish_at_from_kst(
                compilation_schedule_date,
                compilation_schedule_time,
            )
            st.caption("풀영상 예약 시간도 한국 시간(KST) 기준으로 처리됩니다.")
        st.caption(
            "풀영상 업로드가 성공하면 Google Drive에 자동 백업한 뒤, "
            "풀영상 mp4와 썸네일을 로컬에서 자동 삭제합니다."
        )

    compilation_run_button = st.button(
        "풀영상 실행 시작",
        type="primary",
        use_container_width=True,
        key="compilation_run_button",
    )

with comp_right:
    st.subheader("풀영상 미리보기")
    if compilation_levels:
        compilation_preview_rows = get_compilation_preview_rows(
            compilation_levels,
            int(compilation_start_day),
            int(compilation_end_day),
        )
        st.dataframe(compilation_preview_rows, use_container_width=True, hide_index=True)
    else:
        compilation_preview_rows = []
        st.info("최소 한 개 이상의 레벨을 선택해 주세요.")

if compilation_run_button:
    if not compilation_levels:
        st.warning("풀영상 레벨을 하나 이상 선택해 주세요.")
    elif not compilation_range_options:
        st.error("실행 가능한 풀영상 고정 구간이 없습니다.")
    elif compilation_action_mode == "업로드만" and any(
        row["영상 파일"] == "없음" for row in compilation_preview_rows
    ):
        st.error("업로드할 풀영상 파일이 없는 항목이 있어 실행을 시작하지 않았습니다.")
    else:
        with st.spinner("풀영상 작업 실행 중입니다. 시간이 오래 걸릴 수 있습니다."):
            compilation_logs = run_compilation_task(
                compilation_levels,
                compilation_action_mode,
                int(compilation_start_day),
                int(compilation_end_day),
                compilation_privacy_status,
                compilation_publish_at,
                comp_live_log_placeholder,
                comp_status_placeholder,
                comp_progress_bar,
            )

        st.success("풀영상 작업이 완료되었습니다.")
        st.subheader("풀영상 실행 로그")
        st.code(compilation_logs or "기록된 로그가 없습니다.", language="text")
