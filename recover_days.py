import argparse

import main


def parse_levels(raw_levels):
    return [level.strip().upper() for level in raw_levels.split(",") if level.strip()]


def parse_range(start_day, end_day):
    if start_day > end_day:
        raise ValueError("start_day must be less than or equal to end_day")
    return range(start_day, end_day + 1)


def regenerate_days(levels, start_day, end_day):
    for level in levels:
        for day in parse_range(start_day, end_day):
            print(f"[REGENERATE] {level} DAY {day:03d}")
            main.regenerate_existing_day(level, day)


def restore_days(levels, start_day, end_day, overwrite=True):
    for level in levels:
        for day in parse_range(start_day, end_day):
            print(f"[RESTORE] {level} DAY {day:03d}")
            try:
                main.restore_existing_day_from_drive(level, day, overwrite=overwrite)
            except Exception as error:
                print(f"[RESTORE FAILED] {level} DAY {day:03d}: {error}")


def main_cli():
    parser = argparse.ArgumentParser(description="DAY 영상 복구 도구")
    parser.add_argument("--levels", required=True, help="예: N1,N2,N3,N4,N5")
    parser.add_argument("--start-day", type=int, required=True, help="시작 DAY")
    parser.add_argument("--end-day", type=int, required=True, help="끝 DAY")
    parser.add_argument(
        "--mode",
        choices=["regenerate", "restore", "both"],
        default="both",
        help="regenerate=CSV day 기준 재생성, restore=Drive 복원, both=둘 다",
    )
    parser.add_argument(
        "--no-overwrite",
        action="store_true",
        help="기존 파일이 있으면 Drive 복원을 건너뜁니다.",
    )

    args = parser.parse_args()

    levels = parse_levels(args.levels)
    overwrite = not args.no_overwrite

    if args.mode in {"regenerate", "both"}:
        regenerate_days(levels, args.start_day, args.end_day)

    if args.mode in {"restore", "both"}:
        restore_days(levels, args.start_day, args.end_day, overwrite=overwrite)


if __name__ == "__main__":
    main_cli()
