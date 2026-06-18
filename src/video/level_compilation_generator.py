# ==================================================
# 파일명: level_compilation_generator.py
# 역할: 레벨별 DAY 영상을 하나의 긴 영상으로 묶는 모듈
# 예시: N1_DAY_001.mp4 ~ N1_DAY_025.mp4 합치기
# ==================================================

import os

from moviepy import VideoFileClip, concatenate_videoclips

from src.image.level_thumbnail_generator import generate_level_thumbnail


# ==================================================
# 1. 기본 설정
# ==================================================

DAY_VIDEO_FOLDER = "output/day_videos"

OUTPUT_FOLDER = "output/compilations"


# ==================================================
# 2. 출력 폴더 생성
# ==================================================

def ensure_output_folder():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)


# ==================================================
# 3. DAY 영상 경로 만들기
# ==================================================

def build_day_video_path(level, day):
    day_text = str(day).zfill(3)

    filename = f"{level}_DAY_{day_text}.mp4"

    video_path = os.path.join(
        DAY_VIDEO_FOLDER,
        level,
        filename
    )

    return video_path


# ==================================================
# 4. 묶음 영상 파일명 만들기
# ==================================================

def build_compilation_output_path(level, start_day, end_day):
    start_day_text = str(start_day).zfill(3)
    end_day_text = str(end_day).zfill(3)

    filename = f"{level}_DAY_{start_day_text}_{end_day_text}_FULL.mp4"

    output_path = os.path.join(
        OUTPUT_FOLDER,
        filename
    )

    return output_path


# ==================================================
# 5. 레벨별 묶음 영상 생성
# ==================================================

def create_level_compilation(
    level="N1",
    start_day=1,
    end_day=25
):
    ensure_output_folder()

    clips = []

    print("묶음 영상 생성을 시작합니다.")
    print("레벨:", level)
    print("시작 DAY:", start_day)
    print("끝 DAY:", end_day)

    for day in range(start_day, end_day + 1):
        video_path = build_day_video_path(
            level=level,
            day=day
        )

        if not os.path.exists(video_path):
            print("파일 없음, 건너뜀:", video_path)
            continue

        print("추가:", video_path)

        clip = VideoFileClip(video_path)
        clips.append(clip)

    if not clips:
        print("합칠 영상이 없습니다.")
        return {
            "video_path": "",
            "thumbnail_path": "",
            "level": level,
            "start_day": start_day,
            "end_day": end_day
        }

    final_clip = concatenate_videoclips(
        clips,
        method="compose"
    )

    output_path = build_compilation_output_path(
        level=level,
        start_day=start_day,
        end_day=end_day
    )

    final_clip.write_videofile(
        output_path,
        fps=24,
        codec="libx264",
        audio_codec="aac"
    )

    for clip in clips:
        clip.close()

    final_clip.close()

    thumbnail_path = generate_level_thumbnail(
        level=level,
        start_day=start_day,
        end_day=end_day
    )

    print("묶음 영상 생성 완료:", output_path)
    print("묶음 썸네일 생성 완료:", thumbnail_path)

    return {
        "video_path": output_path,
        "thumbnail_path": thumbnail_path,
        "level": level,
        "start_day": start_day,
        "end_day": end_day
    }


# ==================================================
# 6. 전체 레벨 묶음 영상 생성
# ==================================================

def create_all_level_compilations(
    start_day=1,
    end_day=25
):
    levels = ["N1", "N2", "N3", "N4", "N5"]

    results = []

    for level in levels:
        result = create_level_compilation(
            level=level,
            start_day=start_day,
            end_day=end_day
        )

        results.append(result)

    return results


# ==================================================
# 7. 테스트 실행
# ==================================================

if __name__ == "__main__":
    create_level_compilation(
        level="N1",
        start_day=1,
        end_day=25
    )