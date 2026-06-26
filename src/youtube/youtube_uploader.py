# ==================================================
# File: youtube_uploader.py
# Role: YouTube login and shorts upload utility
# ==================================================

import os
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from src.youtube.upload_log import get_upload_entry, is_uploaded, save_uploaded, update_uploaded_entry

SCOPES = ["https://www.googleapis.com/auth/youtube"]

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
    "BUSINESS": "PLMF1atgZjG1g",
}

BUSINESS_LEVELS = {"BUSINESS"}


def get_publish_time_by_day(day):
    day = int(day)
    kst = ZoneInfo("Asia/Seoul")
    today = datetime.now(kst)
    pair_index = (day - 3) // 1
    publish_date = today + timedelta(days=pair_index + 1)

    if day % 2 == 1:
        publish_time = publish_date.replace(hour=8, minute=0, second=0, microsecond=0)
    else:
        publish_time = publish_date.replace(hour=18, minute=0, second=0, microsecond=0)

    return publish_time.astimezone(ZoneInfo("UTC")).isoformat()


def build_publish_at_from_kst(schedule_date, schedule_time):
    if isinstance(schedule_date, str):
        schedule_date = date.fromisoformat(schedule_date)

    if isinstance(schedule_time, str):
        schedule_time = time.fromisoformat(schedule_time)

    kst = ZoneInfo("Asia/Seoul")
    scheduled = datetime.combine(schedule_date, schedule_time).replace(tzinfo=kst)
    return scheduled.astimezone(ZoneInfo("UTC")).isoformat()


def get_youtube_service():
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        try:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
        except Exception as error:
            error_text = str(error)
            if "invalid_grant" in error_text or "Token has been expired or revoked" in error_text:
                raise RuntimeError(
                    "YouTube 인증이 만료되었거나 해제되었습니다. "
                    "token.json을 다시 발급해야 합니다."
                ) from error
            raise

        with open(TOKEN_FILE, "w", encoding="utf-8") as token_file:
            token_file.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)


def normalize_day(day):
    day_text = str(day).strip()

    if day_text.upper().startswith("DAY"):
        day_text = day_text.upper().replace("DAY", "")
        day_text = day_text.replace("_", "")
        day_text = day_text.replace("-", "")
        day_text = day_text.strip()

    return day_text.zfill(3)


def normalize_level(level):
    level_text = str(level).strip().upper()

    if level_text in BUSINESS_LEVELS:
        return level_text

    if not level_text.startswith("N"):
        level_text = "N" + level_text

    return level_text


def get_level_video_folder(level):
    return os.path.join(VIDEO_FOLDER, normalize_level(level))


def build_upload_info(level, day):
    level = normalize_level(level)
    day = normalize_day(day)

    video_file = os.path.join(get_level_video_folder(level), f"{level}_DAY_{day}.mp4")
    thumbnail_file = os.path.join(THUMBNAIL_FOLDER, f"{level}_DAY_{day}.jpg")

    if level == "BUSINESS":
        title = f"비즈니스 일본어 단어 + 표현 | DAY {day}"
        description = """
#비즈니스일본어 #일본어공부 #일본어표현

비즈니스 일본어 단어와 표현을 함께 학습할 수 있도록 구성한 쇼츠입니다.
단어, 메일 표현, 회의 표현, 전화 응대 표현을 짧게 반복 학습할 수 있도록 구성했습니다.
"""
        tags = ["비즈니스일본어", "일본어공부", "일본어단어", "일본어표현", "일본어쇼츠", "business japanese"]
        return video_file, thumbnail_file, title, description, tags

    title = f"JLPT {level} 일본어 단어 + 문법 | DAY {day}"
    description = f"""
#JLPT #일본어 #{level}

※ 본 영상은 개인적인 학습과 지인의 학습용으로 제작 된 영상이므로 영상에 대한 피드백은 받지 않습니다.

JLPT {level} 일본어 학습
단어 + 문법학습 콘텐츠
"""
    tags = ["JLPT", "일본어", "일본어단어", "일본어공부", "일본어쇼츠", "일본어문법"]
    return video_file, thumbnail_file, title, description, tags


def check_file_exists(file_path, label):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{label} 파일을 찾을 수 없습니다: {file_path}")


def upload_video(youtube, video_file, title, description, thumbnail_file=None, privacy_status=DEFAULT_PRIVACY_STATUS, publish_at=None, tags=None):
    check_file_exists(video_file, "영상")

    if tags is None:
        tags = ["일본어", "일본어공부", "일본어쇼츠"]

    request_body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "27",
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }

    if publish_at:
        request_body["status"]["publishAt"] = publish_at
        request_body["status"]["privacyStatus"] = "private"

    media_file = MediaFileUpload(video_file, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=request_body, media_body=media_file)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print("업로드 진행률:", f"{int(status.progress() * 100)}%")

    video_id = response["id"]
    print("업로드 완료")
    print("VIDEO ID:", video_id)

    if thumbnail_file:
        if os.path.exists(thumbnail_file):
            try:
                youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(thumbnail_file)).execute()
                print("썸네일 등록 완료")
            except Exception as error:
                print("썸네일 등록 실패")
                print(error)
        else:
            print("썸네일 파일 없음. 등록 건너뜀:", thumbnail_file)

    return video_id


def get_video_details(youtube, video_id):
    response = youtube.videos().list(part="snippet,status", id=video_id).execute()
    items = response.get("items", [])
    if not items:
        raise ValueError(f"유튜브 영상 정보를 찾을 수 없습니다: {video_id}")

    return items[0]


def add_video_to_playlist(youtube, video_id, playlist_id):
    request_body = {
        "snippet": {
            "playlistId": playlist_id,
            "resourceId": {
                "kind": "youtube#video",
                "videoId": video_id,
            },
        }
    }

    youtube.playlistItems().insert(part="snippet", body=request_body).execute()
    print("재생목록 등록 완료")


def find_video_id_by_level_day(youtube, level, day):
    _, _, title, _, _ = build_upload_info(level, day)
    response = youtube.search().list(
        part="id,snippet",
        forMine=True,
        type="video",
        maxResults=10,
        q=title,
    ).execute()

    for item in response.get("items", []):
        snippet = item.get("snippet", {})
        if snippet.get("title") == title:
            video_id = item.get("id", {}).get("videoId")
            if video_id:
                return video_id

    return None


def resolve_video_id(youtube, level, day):
    upload_key = f"{normalize_level(level)}_DAY_{normalize_day(day)}"
    entry = get_upload_entry(upload_key)

    if entry and entry.get("video_id"):
        return entry["video_id"]

    video_id = find_video_id_by_level_day(youtube, level, day)
    if video_id:
        update_uploaded_entry(
            upload_key,
            uploaded=True,
            video_id=video_id,
            level=normalize_level(level),
            day=normalize_day(day),
        )

    return video_id


def fetch_video_schedule_by_level_day(level, day):
    level = normalize_level(level)
    day = normalize_day(day)
    upload_key = f"{level}_DAY_{day}"
    youtube = get_youtube_service()
    video_id = resolve_video_id(youtube, level, day)

    if not video_id:
        raise ValueError(f"{upload_key}에 연결된 YouTube 영상 ID를 찾지 못했습니다.")

    video = get_video_details(youtube, video_id)
    snippet = video.get("snippet", {})
    status = video.get("status", {})

    publish_at = status.get("publishAt")
    privacy_status = status.get("privacyStatus", DEFAULT_PRIVACY_STATUS)

    update_uploaded_entry(
        upload_key,
        uploaded=True,
        video_id=video_id,
        level=level,
        day=day,
        privacy_status=privacy_status,
        publish_at=publish_at,
        title=snippet.get("title", ""),
    )

    return {
        "upload_key": upload_key,
        "video_id": video_id,
        "privacy_status": privacy_status,
        "publish_at": publish_at,
        "title": snippet.get("title", ""),
    }


def update_video_schedule_by_level_day(level, day, privacy_status=DEFAULT_PRIVACY_STATUS, publish_at=None):
    level = normalize_level(level)
    day = normalize_day(day)
    upload_key = f"{level}_DAY_{day}"
    youtube = get_youtube_service()
    video_id = resolve_video_id(youtube, level, day)

    if not video_id:
        raise ValueError(f"{upload_key}에 연결된 YouTube 영상 ID를 찾지 못했습니다.")

    video = get_video_details(youtube, video_id)
    snippet = video.get("snippet", {})
    status = video.get("status", {})

    updated_status = {
        "privacyStatus": privacy_status,
        "selfDeclaredMadeForKids": status.get("selfDeclaredMadeForKids", False),
    }

    if publish_at:
        updated_status["publishAt"] = publish_at
        updated_status["privacyStatus"] = "private"

    request_body = {
        "id": video_id,
        "snippet": {
            "title": snippet.get("title", ""),
            "description": snippet.get("description", ""),
            "tags": snippet.get("tags", []),
            "categoryId": snippet.get("categoryId", "27"),
        },
        "status": updated_status,
    }

    youtube.videos().update(part="snippet,status", body=request_body).execute()

    update_uploaded_entry(
        upload_key,
        uploaded=True,
        video_id=video_id,
        level=level,
        day=day,
        privacy_status=updated_status["privacyStatus"],
        publish_at=publish_at,
        title=snippet.get("title", ""),
    )

    return video_id


def upload_by_level_day(level, day, privacy_status=DEFAULT_PRIVACY_STATUS, publish_at=None):
    level = normalize_level(level)
    day = normalize_day(day)

    if publish_at is None:
        publish_at = get_publish_time_by_day(day)

    upload_key = f"{level}_DAY_{day}"
    if is_uploaded(upload_key):
        print("이미 업로드 완료:", upload_key)
        return None

    youtube = get_youtube_service()
    video_file, thumbnail_file, title, description, tags = build_upload_info(level, day)

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
        publish_at=publish_at,
        tags=tags,
    )

    playlist_id = PLAYLIST_MAP.get(level)
    if playlist_id:
        add_video_to_playlist(youtube=youtube, video_id=video_id, playlist_id=playlist_id)

    save_uploaded(
        upload_key,
        video_id=video_id,
        level=level,
        day=day,
        privacy_status="private" if publish_at else privacy_status,
        publish_at=publish_at,
        title=title,
    )
    return video_id
