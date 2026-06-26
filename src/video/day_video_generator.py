# ==================================================
# 파일명: day_video_generator.py
# 역할: 단어별 mp4 영상을 하나로 합쳐 레벨별 DAY 쇼츠 영상을 생성하는 모듈
# ==================================================


# ==================================================
# 1. 라이브러리 import 섹션
# ==================================================

import os
import json

from moviepy import VideoFileClip, concatenate_videoclips
from src.data.day_manager import get_current_day_filename
from src.utils.filename_utils import resolve_romaji_file_path


# ==================================================
# 2. 기본 경로 설정 섹션
# ==================================================

WORDS_FILE = "data/words.json"

WORD_VIDEO_FOLDER = "output/videos"

DAY_VIDEO_FOLDER = "output/day_videos"


def get_level_day_video_folder(level):
    level = str(level).strip().upper()
    return os.path.join(DAY_VIDEO_FOLDER, level)


if not os.path.exists(DAY_VIDEO_FOLDER):
    os.makedirs(DAY_VIDEO_FOLDER)


# ==================================================
# 3. words.json 불러오기 함수 섹션
# ==================================================

def load_words():
    try:
        with open(WORDS_FILE, "r", encoding="utf-8") as file:
            words = json.load(file)
            return words

    except FileNotFoundError:
        print("words.json 파일을 찾을 수 없습니다.")
        return []

    except json.JSONDecodeError:
        print("words.json 형식이 올바르지 않습니다.")
        return []


# ==================================================
# 4. 단어별 영상 경로 만들기 함수 섹션
# ==================================================

def get_word_video_path(current_word):
    romaji = current_word.get("romaji", "")

    if not romaji:
        print("romaji 값이 없어서 영상 경로를 만들 수 없습니다.")
        return ""

    video_path = resolve_romaji_file_path(
        WORD_VIDEO_FOLDER,
        romaji,
        ".mp4"
    )

    if not os.path.exists(video_path):
        print("단어 영상 파일을 찾을 수 없습니다:", video_path)
        return ""

    return video_path


# ==================================================
# 5. DAY 영상 생성 함수 섹션
# ==================================================

def create_day_video(level="N1"):
    words = load_words()

    if not words:
        print(level, "DAY 영상에 사용할 데이터가 없습니다.")
        return ""

    clips = []

    for current_word in words:
        print(current_word)
        video_path = get_word_video_path(current_word)

        if not video_path:
            continue

        clip = VideoFileClip(video_path)
        clips.append(clip)
        
        print("추가된 영상:", video_path)

    print("총 클립 개수:", len(clips))

    if not clips:
        print(level, "연결할 영상 클립이 없습니다.")
        return ""

    final_clip = concatenate_videoclips(
        clips,
        method="compose"
    )

    day_video_name = get_current_day_filename(level)

    save_path = os.path.join(
        get_level_day_video_folder(level),
        day_video_name
    )

    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    final_clip.write_videofile(
        save_path,
        fps=24,
        codec="libx264",
        audio_codec="aac"
    )

    for clip in clips:
        clip.close()

    final_clip.close()

    print(level, "DAY 영상 생성 완료:", save_path)

    return save_path


# ==================================================
# 6. 테스트 실행 섹션
# ==================================================

if __name__ == "__main__":
    create_day_video("N1")
