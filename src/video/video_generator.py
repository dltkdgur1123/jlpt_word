# ==================================================
# 파일명: video_generator.py
# 역할: 단어 이미지와 TTS 음성을 합쳐 JLPT 쇼츠 mp4 영상을 생성하는 모듈
# ==================================================


# ==================================================
# 1. 라이브러리 import 섹션
# ==================================================


import os

from moviepy import ImageClip, AudioFileClip, concatenate_audioclips
from src.utils.filename_utils import (
    normalize_romaji_filename,
    resolve_romaji_file_path,
)


# ==================================================
# 2. 기본 경로 설정 섹션
# ==================================================


# - 완성된 단어 카드 이미지가 있는 폴더
image_folder = "assets/images"


# - 일본어 / 한국어 mp3 파일이 있는 폴더
audio_folder = "assets/audio"


# - 완성된 mp4 쇼츠 영상을 저장할 폴더
video_folder = "output/videos"


if not os.path.exists(video_folder):
    os.makedirs(video_folder)


SAFE_AUDIO_TAIL_SECONDS = 0.05


# ==================================================
# 3. 단어 영상 생성 함수 섹션
# ==================================================


# - romaji 값을 받는다.
# - 단어 이미지 경로를 만든다.
# - 일본어 mp3 경로를 만든다.
# - 한국어 mp3 경로를 만든다.
# - 영상 저장 경로를 만든다.
# - 이미지/오디오 파일이 있는지 확인한다.
# - 일본어 음성과 한국어 음성을 연결한다.
# - 이미지 클립에 오디오를 붙인다.
# - mp4 파일로 저장한다.


# 단어 1개에 대한 쇼츠 영상생성 함수
def create_word_video(romaji):
    safe_romaji = normalize_romaji_filename(romaji)

    image_path = resolve_romaji_file_path(image_folder, romaji, ".png")

    jp_audio_path = resolve_romaji_file_path(
        audio_folder,
        f"{romaji}_jp",
        ".mp3"
    )

    kr_audio_path = resolve_romaji_file_path(
        audio_folder,
        f"{romaji}_kr",
        ".mp3"
    )

    video_path = os.path.join(
        video_folder,
        safe_romaji + ".mp4"
    )


    # 이미지, 오디오 파일이 없으면 영상 생성 중단
    if not os.path.exists(image_path):

        print("이미지 파일을 찾을 수 없습니다:", image_path)

        return ""


    if not os.path.exists(jp_audio_path):

        print("일본어 오디오 파일을 찾을 수 없습니다:", jp_audio_path)

        return ""


    if not os.path.exists(kr_audio_path):

        print("한국어 오디오 파일을 찾을 수 없습니다:", kr_audio_path)

        return ""


    jp_audio = None
    kr_audio = None
    final_audio = None
    trimmed_audio = None
    image_clip = None

    try:
        # mp3 파일을 moviepy 오디오 클립으로 변환
        jp_audio = AudioFileClip(jp_audio_path)
        kr_audio = AudioFileClip(kr_audio_path)

        # 일본어 음성 + 한국어 음성을 하나의 오디오로 연결 (음성 반복 역할)
        final_audio = concatenate_audioclips([
            jp_audio,
            kr_audio,
            jp_audio,
            kr_audio,
            jp_audio,
            kr_audio
        ])

        # MoviePy가 클립 끝단을 아주 조금 넘어 읽는 상황을 막기 위해
        # 실제 길이보다 짧은 안전 구간만 사용한다.
        safe_duration = max(0, final_audio.duration - SAFE_AUDIO_TAIL_SECONDS)

        if safe_duration <= 0:
            raise ValueError(
                f"오디오 길이가 너무 짧아 영상을 만들 수 없습니다: {romaji}"
            )

        trimmed_audio = final_audio.subclipped(0, safe_duration)

        # 단어 이미지 파일을 영상 클립으로 변환
        image_clip = ImageClip(image_path).with_duration(safe_duration)

        # 이미지 클립에 최종 오디오를 붙인다.
        image_clip = image_clip.with_audio(trimmed_audio)

        # 최종 mp4 파일로 저장한다.
        image_clip.write_videofile(
            video_path,
            fps=24,
            codec="libx264",
            audio_codec="aac"
        )

        print("영상 생성 완료:", video_path)

        return video_path

    finally:
        if image_clip is not None:
            image_clip.close()

        if trimmed_audio is not None:
            trimmed_audio.close()

        if final_audio is not None:
            final_audio.close()

        if jp_audio is not None:
            jp_audio.close()

        if kr_audio is not None:
            kr_audio.close()


# ==================================================
# 4. 특수문자 제거
# ==================================================




# ==================================================
# 5. 테스트 실행 섹션
# ==================================================

# - 이 파일을 직접 실행했을 때 테스트한다.
# - gakkou 단어 영상 하나를 만든다.


if __name__ == "__main__":
    create_word_video("gakkou")
