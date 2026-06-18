# ==================================================
# 파일명: youtube_uploader.py
# 역할: YouTube API 로그인, 영상 업로드, 썸네일 등록을 담당하는 도구
# ==================================================


# ==================================================
# 1. 라이브러리 import 섹션
# ==================================================

import os
import time

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from src.youtube.upload_log import (is_uploaded,save_uploaded)
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


# ==================================================
# 2. 기본 설정 섹션
# ==================================================

SCOPES = [
    "https://www.googleapis.com/auth/youtube"
]

CLIENT_SECRET_FILE = "client_secret.json"
TOKEN_FILE = "token.json"

VIDEO_FOLDER = "output/day_videos"
THUMBNAIL_FOLDER = "output/thumbnails"

DEFAULT_PRIVACY_STATUS = "private"

PLAYLIST_MAP = {
    "N1": "PLh6NdYu4HOYcrOMwmN2XRGb9lljlErfCy",
    "N2": "PLh6NdYu4HOYfO0Tg1RhW9_pRV7LCei22o",
    "N3": "PLh6NdYu4HOYfEzGwpjvxjYFyqlmlxJQ-c",
    "N4": "PLh6NdYu4HOYelTuFXOmAX0Y88LZHXZl_o",
    "N5": "PLh6NdYu4HOYdGBr5ZMNAIxhPttSo_tYSg",
}


# ==================================================
# DAY 번호 기준 예약 공개 시간 계산
# ==================================================

def get_publish_time_by_day(day):

    day = int(day)

    kst = ZoneInfo("Asia/Seoul")

    today = datetime.now(kst)

    pair_index = (day - 3) // 1

    publish_date = today + timedelta(days=pair_index + 1)

    if day % 2 == 1:
        publish_time = publish_date.replace(
            hour=8,
            minute=0,
            second=0,
            microsecond=0
        )
    else:
        publish_time = publish_date.replace(
            hour=18,
            minute=0,
            second=0,
            microsecond=0
        )

    publish_time_utc = publish_time.astimezone(
        ZoneInfo("UTC")
    )

    return publish_time_utc.isoformat()





# ==================================================
# 3. YouTube 로그인 서비스 생성 함수 섹션
# ==================================================

def get_youtube_service():
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(
            TOKEN_FILE,
            SCOPES
        )

    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET_FILE,
                SCOPES
            )

            creds = flow.run_local_server(
                port=0
            )

        with open(
            TOKEN_FILE,
            "w",
            encoding="utf-8"
        ) as token_file:
            token_file.write(
                creds.to_json()
            )

    youtube = build(
        "youtube",
        "v3",
        credentials=creds
    )

    return youtube


# ==================================================
# 4. DAY 숫자 정리 함수 섹션
# ==================================================

def normalize_day(day):
    day_text = str(day).strip()

    if day_text.upper().startswith("DAY"):
        day_text = day_text.upper().replace("DAY", "")
        day_text = day_text.replace("_", "")
        day_text = day_text.replace("-", "")
        day_text = day_text.strip()

    return day_text.zfill(3)


# ==================================================
# 5. 레벨 정리 함수 섹션
# ==================================================

def normalize_level(level):
    level_text = str(level).strip().upper()

    if not level_text.startswith("N"):
        level_text = "N" + level_text

    return level_text


# ==================================================
# 6. 업로드 정보 생성 함수 섹션
# ==================================================

def build_upload_info(level, day):
    level = normalize_level(level)
    day = normalize_day(day)

    video_file = os.path.join(
        VIDEO_FOLDER,
        f"{level}_DAY_{day}.mp4"
    )

    thumbnail_file = os.path.join(
        THUMBNAIL_FOLDER,
        f"{level}_DAY_{day}.jpg"
    )


    title = f"JLPT {level} 일본어 단어 + 문법 | DAY {day}"

    description = f"""

#JLPT #일본어 #{level}

※ 본 영상은 개인적인 학습과 지인의 학습용으로 제작 된 영상이므로 영상에 대한 피드백은 받지 않습니다. 

JLPT {level} 일본어 학습

단어 + 문법학습 콘텐츠

"""

    return video_file, thumbnail_file, title, description


# ==================================================
# 7. 파일 존재 확인 함수 섹션
# ==================================================

def check_file_exists(file_path, label):
    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"{label} 파일을 찾을 수 없습니다: {file_path}"
        )


# ==================================================
# 8. 영상 업로드 함수 섹션
# ==================================================

def upload_video(
    youtube,
    video_file,
    title,
    description,
    thumbnail_file=None,
    privacy_status=DEFAULT_PRIVACY_STATUS,
    publish_at=None,
    tags=None
):
    check_file_exists(
        video_file,
        "영상"
    )

    if tags is None:
        tags = [
            "JLPT",
            "일본어",
            "일본어단어",
            "일본어공부",
            "일본어쇼츠",
            "일본어문법"
        ]

    request_body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "27"
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False
        }
    }

    if publish_at:
        request_body["status"]["publishAt"] = publish_at
        request_body["status"]["privacyStatus"] = "private"

    media_file = MediaFileUpload(
        video_file,
        chunksize=-1,
        resumable=True
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media_file
    )

    response = None

    while response is None:
        status, response = request.next_chunk()

        if status:
            print(
                "업로드 진행률:",
                f"{int(status.progress() * 100)}%"
            )

    video_id = response["id"]

    print("업로드 완료")
    print("VIDEO ID:", video_id)

    if thumbnail_file:
        if os.path.exists(thumbnail_file):
            try:
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(thumbnail_file)
                ).execute()

                print("썸네일 등록 완료")

            except Exception as e:
                print("썸네일 등록 실패")
                print(e)
        else:
            print("썸네일 파일 없음. 썸네일 등록 건너뜀:", thumbnail_file)

    return video_id

# 재생목록 자동 등록 함수

def add_video_to_playlist(
    youtube,
    video_id,
    playlist_id
):
    request_body = {
        "snippet": {
            "playlistId": playlist_id,
            "resourceId": {
                "kind": "youtube#video",
                "videoId": video_id
            }
        }
    }

    youtube.playlistItems().insert(
        part="snippet",
        body=request_body
    ).execute()

    print("재생목록 등록 완료")


# ==================================================
# 9. 레벨/DAY 기준 업로드 함수 섹션
# ==================================================

def upload_by_level_day(
    level,
    day,
    privacy_status=DEFAULT_PRIVACY_STATUS,
    publish_at=None
):
    level = normalize_level(level)
    day = normalize_day(day)
    
    if publish_at is None:
        publish_at = get_publish_time_by_day(day)
    
    upload_key = f"{level}_DAY_{day}"

    if is_uploaded(upload_key):
        print("이미 업로드 완료:", upload_key)
        return None

    youtube = get_youtube_service()

    video_file, thumbnail_file, title, description = build_upload_info(
        level,
        day
    )
    
    print("업로드 레벨:", level)
    print("업로드 DAY:", day)
    print("업로드 영상:", video_file)
    print("업로드 썸네일:", thumbnail_file)
    print("업로드 제목:", title)
    
    video_id = upload_video(
        youtube=youtube,
        video_file=video_file,
        title=title,
        description=description,
        thumbnail_file=thumbnail_file,
        privacy_status=privacy_status,
        publish_at=publish_at
    )
    
    playlist_id = PLAYLIST_MAP.get(level)

    if playlist_id:
        add_video_to_playlist(
            youtube=youtube,
            video_id=video_id,
            playlist_id=playlist_id
        )    
    
    
    save_uploaded(upload_key)

    return video_id


# ==================================================
# 10. 로그인 테스트 함수 섹션
# ==================================================

def test_login():
    youtube = get_youtube_service()

    if youtube:
        print("유튜브 로그인 성공")


# ==================================================
# 11. 실전 업로드 함수 섹션
# ==================================================

def upload_today_video(
    level,
    day,
    privacy_status="private"
):
    return upload_by_level_day(
        level=level,
        day=day,
        privacy_status=privacy_status
    )


# ==================================================
# 12. 단독 실행 섹션
# ==================================================

if __name__ == "__main__":
    upload_today_video(
        level="N1",
        day="012",
        privacy_status="private"
    )

# if __name__ == "__main__":
#     test_upload()