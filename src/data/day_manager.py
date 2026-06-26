import json
import os

DAY_STATUS_FILE = os.path.join("data", "day_status.json")

DEFAULT_STATUS = {
    "N1": 1,
    "N2": 1,
    "N3": 1,
    "N4": 1,
    "N5": 1,
    "BUSINESS": 1,
}


def load_day_status():
    if not os.path.exists(DAY_STATUS_FILE):
        return DEFAULT_STATUS.copy()

    try:
        with open(DAY_STATUS_FILE, "r", encoding="utf-8") as file:
            status = json.load(file)
    except json.JSONDecodeError:
        return DEFAULT_STATUS.copy()

    for level, default_day in DEFAULT_STATUS.items():
        if level not in status:
            status[level] = default_day

    return status


def save_day_status(status):
    with open(DAY_STATUS_FILE, "w", encoding="utf-8") as file:
        json.dump(status, file, ensure_ascii=False, indent=4)


def get_current_day_number(level="N1"):
    status = load_day_status()
    return status.get(level, 1)


def get_current_day_text(level="N1"):
    current_day = get_current_day_number(level)
    return f"DAY {current_day:03d}"


def get_current_day_filename(level="N1"):
    current_day = get_current_day_number(level)
    return f"{level}_DAY_{current_day:03d}.mp4"


def increase_day_number(level="N1"):
    status = load_day_status()
    current_day = status.get(level, 1)
    status[level] = current_day + 1
    save_day_status(status)
    print(level, "DAY incremented:", status[level])
