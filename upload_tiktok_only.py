# ==================================================
# 파일명: upload_tiktok_only.py
# 역할: 이미 생성된 output/day_videos 영상을 TikTok에만 업로드하는 실행 파일
# ==================================================

from src.tiktok.tiktok_uploader import upload_tiktok_by_level_day

LEVELS = ["N1", "N2", "N3", "N4", "N5"]
DAY = "001"


if __name__ == "__main__":
    print("TikTok 전용 업로드 시작")

    for level in LEVELS:
        print("현재 업로드 대상:", level, "DAY", DAY)

        upload_tiktok_by_level_day(
            level=level,
            day=DAY
        )

    print("TikTok 전용 업로드 종료")
