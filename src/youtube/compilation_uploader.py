# ==================================================
# 파일명: compilation_uploader.py
# 역할: 25개 단위로 생성된 JLPT 풀영상을 YouTube 일반 영상으로 업로드하는 모듈
# 예시: N1_DAY_001_025_FULL.mp4 업로드
# ==================================================


# ==================================================
# 1. 라이브러리 import 섹션
# ==================================================

import os

from src.youtube.youtube_uploader import (
    get_youtube_service,
    upload_video
)


# ==================================================
# 2. 기본 설정 섹션
# ==================================================

COMPILATION_VIDEO_FOLDER = "output/compilations"
COMPILATION_THUMBNAIL_FOLDER = "output/thumbnails/level"

DEFAULT_PRIVACY_STATUS = "private"


# ==================================================
# 3. DAY 숫자 정리 함수 섹션
# ==================================================

def normalize_day(day):
    return str(day).zfill(3)


# ==================================================
# 4. 풀영상 파일 경로 생성 함수 섹션
# ==================================================

def build_compilation_video_path(level, start_day, end_day):
    start_day_text = normalize_day(start_day)
    end_day_text = normalize_day(end_day)

    filename = f"{level}_DAY_{start_day_text}_{end_day_text}_FULL.mp4"

    video_path = os.path.join(
        COMPILATION_VIDEO_FOLDER,
        filename
    )

    return video_path


# ==================================================
# 5. 풀영상 썸네일 경로 생성 함수 섹션
# ==================================================

def build_compilation_thumbnail_path(level, start_day, end_day):
    start_day_text = normalize_day(start_day)
    end_day_text = normalize_day(end_day)

    filename = f"{level}_DAY_{start_day_text}_{end_day_text}_FULL.jpg"

    thumbnail_path = os.path.join(
        COMPILATION_THUMBNAIL_FOLDER,
        filename
    )

    return thumbnail_path


# ==================================================
# 6. 풀영상 제목 생성 함수 섹션
# ==================================================

def build_compilation_title(level, start_day, end_day):
    start_day_text = normalize_day(start_day)
    end_day_text = normalize_day(end_day)

    title = (
        f"JLPT {level} DAY {start_day_text}~{end_day_text} 몰아보기 "
        f"| 일본어 단어 + 문법"
    )

    return title


# ==================================================
# 7. 풀영상 설명 생성 함수 섹션
# ==================================================

def build_compilation_description(level, start_day, end_day):
    start_day_text = normalize_day(start_day)
    end_day_text = normalize_day(end_day)

    description = f"""JLPT {level} DAY {start_day_text}~{end_day_text} 몰아보기 영상입니다.

일본어 단어와 문법을 한 번에 복습할 수 있도록 구성했습니다.

학습 구성:
- JLPT {level}
- DAY {start_day_text} ~ DAY {end_day_text}
- 일본어 단어
- 일본어 문법
- 반복 청취 학습

#JLPT
#{level}
#일본어
#일본어공부
#일본어단어
#일본어문법
"""

    return description


# ==================================================
# 8. 풀영상 태그 생성 함수 섹션
# ==================================================

def build_compilation_tags(level):
    tags = [
        "JLPT",
        f"JLPT {level}",
        level,
        "일본어",
        "일본어 공부",
        "일본어 단어",
        "일본어 문법",
        "일본어 듣기",
        "일본어 복습",
        "Japanese",
        "Japanese study",
        "Japanese vocabulary",
        "Japanese grammar"
    ]

    return tags


# ==================================================
# 9. 풀영상 업로드 함수 섹션
# ==================================================

def upload_compilation_video(
    level="N1",
    start_day=1,
    end_day=25,
    privacy_status=DEFAULT_PRIVACY_STATUS
):
    video_path = build_compilation_video_path(
        level=level,
        start_day=start_day,
        end_day=end_day
    )

    thumbnail_path = build_compilation_thumbnail_path(
        level=level,
        start_day=start_day,
        end_day=end_day
    )

    if not os.path.exists(video_path):
        print("풀영상 파일을 찾을 수 없습니다:", video_path)
        return None

    if not os.path.exists(thumbnail_path):
        print("풀영상 썸네일을 찾을 수 없습니다:", thumbnail_path)
        thumbnail_path = None

    title = build_compilation_title(
        level=level,
        start_day=start_day,
        end_day=end_day
    )

    description = build_compilation_description(
        level=level,
        start_day=start_day,
        end_day=end_day
    )

    tags = build_compilation_tags(level)

    youtube = get_youtube_service()

    print("풀영상 업로드 시작")
    print("레벨:", level)
    print("영상:", video_path)
    print("썸네일:", thumbnail_path)
    print("제목:", title)

    video_id = upload_video(
        youtube=youtube,
        video_file=video_path,
        title=title,
        description=description,
        thumbnail_file=thumbnail_path,
        privacy_status=privacy_status,
        tags=tags
    )

    print("풀영상 업로드 완료:", video_id)

    return video_id


# ==================================================
# 10. 전체 레벨 풀영상 업로드 함수 섹션
# ==================================================

def upload_all_compilation_videos(
    start_day=1,
    end_day=25,
    privacy_status=DEFAULT_PRIVACY_STATUS
):
    levels = ["N1", "N2", "N3", "N4", "N5"]

    results = []

    for level in levels:
        video_id = upload_compilation_video(
            level=level,
            start_day=start_day,
            end_day=end_day,
            privacy_status=privacy_status
        )

        results.append({
            "level": level,
            "video_id": video_id
        })

    return results


# ==================================================
# 11. 테스트 실행 섹션
# ==================================================

if __name__ == "__main__":
    upload_compilation_video(
        level="N1",
        start_day=1,
        end_day=25,
        privacy_status="private"
    )