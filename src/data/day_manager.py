# ==================================================
# 파일명: day_manager.py
# 역할: JLPT 레벨별 DAY 번호를 저장/조회/증가시키는 모듈
# ==================================================


# ==================================================
# 1. 라이브러리 import 섹션
# ==================================================

import json
import os


# ==================================================
# 2. 기본 설정 섹션
# ==================================================

DAY_STATUS_FILE = os.path.join("data", "day_status.json")

DEFAULT_STATUS = {
    "N1": 1,
    "N2": 1,
    "N3": 1,
    "N4": 1,
    "N5": 1
}


# ==================================================
# 3. DAY 상태 불러오기 함수 섹션
# ==================================================

def load_day_status():
    if not os.path.exists(DAY_STATUS_FILE):
        return DEFAULT_STATUS.copy()

    try:
        with open(DAY_STATUS_FILE, "r", encoding="utf-8") as file:
            status = json.load(file)

        for level in DEFAULT_STATUS:
            if level not in status:
                status[level] = 1

        return status

    except json.JSONDecodeError:
        return DEFAULT_STATUS.copy()


# ==================================================
# 4. DAY 상태 저장 함수 섹션
# ==================================================

def save_day_status(status):
    with open(DAY_STATUS_FILE, "w", encoding="utf-8") as file:
        json.dump(
            status,
            file,
            ensure_ascii=False,
            indent=4
        )


# ==================================================
# 5. 현재 DAY 번호 조회 함수 섹션
# ==================================================

def get_current_day_number(level="N1"):
    status = load_day_status()

    current_day = status.get(level, 1)

    return current_day


# ==================================================
# 6. 현재 DAY 텍스트 조회 함수 섹션
# ==================================================

def get_current_day_text(level="N1"):
    current_day = get_current_day_number(level)

    day_text = f"DAY {current_day:03d}"

    return day_text


# ==================================================
# 7. 현재 DAY 파일명 조회 함수 섹션
# ==================================================

def get_current_day_filename(level="N1"):
    current_day = get_current_day_number(level)

    filename = f"{level}_DAY_{current_day:03d}.mp4"

    return filename


# ==================================================
# 8. DAY 번호 증가 함수 섹션
# ==================================================

def increase_day_number(level="N1"):
    status = load_day_status()

    current_day = status.get(level, 1)

    status[level] = current_day + 1

    save_day_status(status)

    print(level, "DAY 번호 증가 완료:", status[level])


# ==================================================
# 9. 테스트 실행 섹션
# ==================================================

if __name__ == "__main__":
    print("현재 N1 DAY 번호:", get_current_day_number("N1"))
    print("현재 N1 DAY 표시:", get_current_day_text("N1"))
    print("현재 N1 DAY 파일명:", get_current_day_filename("N1"))

    print("현재 N2 DAY 번호:", get_current_day_number("N2"))
    print("현재 N2 DAY 표시:", get_current_day_text("N2"))
    print("현재 N2 DAY 파일명:", get_current_day_filename("N2"))