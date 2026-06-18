# ==================================================
# 파일명: video_generator.py
# 역할: 단어 이미지와 TTS 음성을 합쳐 JLPT 쇼츠 mp4 영상을 생성하는 모듈
# ==================================================


# ==================================================
# 1. 라이브러리 import 섹션
# ==================================================


import os

from moviepy import ImageClip, AudioFileClip, concatenate_audioclips


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
    image_path = os.path.join(
        image_folder,
        romaji + ".png"
    )

    jp_audio_path = os.path.join(
        audio_folder,
        romaji + "_jp.mp3"
    )

    kr_audio_path = os.path.join(
        audio_folder,
        romaji + "_kr.mp3"
    )

    video_path = os.path.join(
        video_folder,
        romaji + ".mp4"
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


    # 영상길이를 오디오 길이에 맞추기 위해 사용
    duration = final_audio.duration - 0.1

    # 단어 이미지 파일을 영상 클립으로 변환
    image_clip = ImageClip(image_path)

    image_clip = image_clip.with_duration(duration)


    # 이미지 클립에 최종 오디오를 붙인다.
    image_clip = image_clip.with_audio(final_audio)



    # 최종 mp4 파일로 저장한다.
    image_clip.write_videofile(video_path, fps=24, codec="libx264", audio_codec="aac")


    print("영상 생성 완료:", video_path)

    return video_path


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