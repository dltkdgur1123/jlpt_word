# ==================================================
# 파일명: main.py
# 역할: JLPT 단어 쇼츠 자동생성 전체 파이프라인 실행 모듈
# ==================================================


# ==================================================
# 1. 라이브러리 import 섹션
# ==================================================

import os
import asyncio

from src.image.image_generator import generate_images
from src.tts.tts_generator import generate_tts_from_words
from src.video.video_batch_generator import generate_all_videos
from src.data.jlpt_word_provider import add_daily_items
from src.data.day_manager import increase_day_number, get_current_day_number
from src.video.day_video_generator import create_day_video
from src.image.thumbnail_generator import generate_thumbnail
from src.youtube.youtube_uploader import (upload_by_level_day)
from src.data.meaning_cleaner import clean_all

# ==================================================
# 2. 기본 설정 섹션
# ==================================================

# LEVELS = ["N1", "N2", "N3", "N4", "N5"]  
LEVELS = ["N4", "N5"] # 업로드 순서가 꼬여서 임시로 주석처리
AUTO_UPLOAD = True
COMPILATION_UNIT = 25
DAY_VIDEO_FOLDER = "output/day_videos"


# ==================================================
# 3. 전체 파이프라인 실행 함수 섹션
# ==================================================

def get_compilation_range(day, unit=COMPILATION_UNIT):
    start_day = ((day - 1) // unit) * unit + 1
    end_day = start_day + unit - 1

    return start_day, end_day


def has_all_day_videos(level, start_day, end_day):
    for day in range(start_day, end_day + 1):
        day_text = str(day).zfill(3)

        video_path = os.path.join(
            DAY_VIDEO_FOLDER,
            level,
            f"{level}_DAY_{day_text}.mp4"
        )

        if not os.path.exists(video_path):
            print("묶음 영상 대기 / 없는 파일:", video_path)
            return False

    return True


def run_pipeline(level):
    print(level, "처리 시작")

    day = get_current_day_number(level)
    day_text = str(day).zfill(3)

    print(level, "현재 DAY:", day_text)
    
    print("준비단계: CSV meaning 정리를 시작합니다.")
    clean_all()
    print("준비단계 완료: CSV meaning 정리 완료")

    print("0단계: 오늘 사용할 단어/문법을 CSV에서 추가합니다.")
    add_daily_items(level)
    print("0단계 완료: 오늘 콘텐츠 추가 완료")

    print("1단계: 단어 카드 이미지 생성을 시작합니다.")
    generate_images()
    print("1단계 완료: 단어 카드 이미지 생성 완료")

    print("2단계: TTS 음성 생성을 시작합니다.")
    asyncio.run(generate_tts_from_words())
    print("2단계 완료: TTS 음성 생성 완료")

    print("3단계: 쇼츠 영상 생성을 시작합니다.")
    generate_all_videos()
    print("3단계 완료: 쇼츠 영상 생성 완료")

    print("4단계: DAY 최종 영상 생성을 시작합니다.")
    create_day_video(level)
    print("4단계 완료: DAY 최종 영상 생성 완료")

    print("5단계: 썸네일 생성을 시작합니다.")
    generate_thumbnail(
        level=level,
        day=day_text
    )
    print("5단계 완료: 썸네일 생성 완료")

    if AUTO_UPLOAD:
        print("6단계: YouTube 업로드를 시작합니다.")
        upload_by_level_day(
            level=level,
            day=day_text,
            privacy_status="private",
        )
        print("6단계 완료: YouTube 업로드 완료")
        

    increase_day_number(level)

    print(level, "전체 파이프라인이 완료되었습니다.")


# ==================================================
# 4. 직접 실행 섹션
# ==================================================

if __name__ == "__main__":
    print("main.py 실행 시작")

    for level in LEVELS:
        print("현재 레벨:", level)

        run_pipeline(level)

    print("main.py 실행 끝")