import mimetypes
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from src.youtube.upload_log import update_uploaded_entry


DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.file"]
CLIENT_SECRET_FILE = "client_secret.json"
DRIVE_TOKEN_FILE = "drive_token.json"

DAY_VIDEO_ROOT = Path("output/day_videos")
THUMBNAIL_ROOT = Path("output/thumbnails")
COMPILATION_VIDEO_ROOT = Path("output/compilations")
COMPILATION_THUMBNAIL_ROOT = Path("output/thumbnails/level")
ROOT_FOLDER_NAME = "jlpt_word_backups"


def get_drive_service():
    creds = None

    if os.path.exists(DRIVE_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(DRIVE_TOKEN_FILE, DRIVE_SCOPES)

    if not creds or not creds.valid:
        try:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, DRIVE_SCOPES)
                creds = flow.run_local_server(port=0)
        except Exception as error:
            error_text = str(error)
            if "invalid_grant" in error_text or "Token has been expired or revoked" in error_text:
                raise RuntimeError(
                    "Google Drive 인증이 만료되었거나 해제되었습니다. drive_token.json을 다시 발급해야 합니다."
                ) from error
            raise

        with open(DRIVE_TOKEN_FILE, "w", encoding="utf-8") as token_file:
            token_file.write(creds.to_json())

    return build("drive", "v3", credentials=creds)


def find_folder(service, folder_name, parent_id=None):
    query_parts = [
        "mimeType = 'application/vnd.google-apps.folder'",
        f"name = '{folder_name}'",
        "trashed = false",
    ]

    if parent_id:
        query_parts.append(f"'{parent_id}' in parents")

    response = service.files().list(
        q=" and ".join(query_parts),
        spaces="drive",
        fields="files(id, name)",
        pageSize=10,
    ).execute()

    files = response.get("files", [])
    return files[0]["id"] if files else None


def ensure_folder(service, folder_name, parent_id=None):
    folder_id = find_folder(service, folder_name, parent_id=parent_id)
    if folder_id:
        return folder_id

    metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parent_id:
        metadata["parents"] = [parent_id]

    folder = service.files().create(body=metadata, fields="id").execute()
    return folder["id"]


def upload_file(service, file_path, parent_id):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"백업할 파일을 찾을 수 없습니다: {file_path}")

    mime_type, _ = mimetypes.guess_type(file_path)
    media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
    metadata = {
        "name": os.path.basename(file_path),
        "parents": [parent_id],
    }

    created = service.files().create(
        body=metadata,
        media_body=media,
        fields="id, name, webViewLink",
    ).execute()

    return created


def delete_local_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False


def build_day_asset_paths(level, day):
    day_text = str(day).zfill(3)
    level_text = str(level).strip().upper()

    return {
        "video": DAY_VIDEO_ROOT / level_text / f"{level_text}_DAY_{day_text}.mp4",
        "thumbnail": THUMBNAIL_ROOT / f"{level_text}_DAY_{day_text}.jpg",
    }


def backup_day_assets(level, day, delete_local=False):
    level_text = str(level).strip().upper()
    day_text = str(day).zfill(3)
    upload_key = f"{level_text}_DAY_{day_text}"
    paths = build_day_asset_paths(level_text, day_text)

    service = get_drive_service()
    root_folder_id = ensure_folder(service, ROOT_FOLDER_NAME)
    shorts_folder_id = ensure_folder(service, "shorts", parent_id=root_folder_id)
    level_folder_id = ensure_folder(service, level_text, parent_id=shorts_folder_id)
    day_folder_id = ensure_folder(service, f"DAY_{day_text}", parent_id=level_folder_id)

    uploaded_files = {}
    for file_type, file_path in paths.items():
        uploaded_files[file_type] = upload_file(service, str(file_path), day_folder_id)

    update_uploaded_entry(
        upload_key,
        drive_backed_up=True,
        drive_folder_id=day_folder_id,
        drive_video_file_id=uploaded_files["video"]["id"],
        drive_video_link=uploaded_files["video"].get("webViewLink"),
        drive_thumbnail_file_id=uploaded_files["thumbnail"]["id"],
        drive_thumbnail_link=uploaded_files["thumbnail"].get("webViewLink"),
    )

    deleted_files = {}
    if delete_local:
        for file_type, file_path in paths.items():
            deleted_files[file_type] = delete_local_file(str(file_path))

    return {
        "upload_key": upload_key,
        "drive_folder_id": day_folder_id,
        "uploaded_files": uploaded_files,
        "deleted_files": deleted_files,
    }


def build_compilation_asset_paths(level, start_day, end_day):
    level_text = str(level).strip().upper()
    start_day_text = str(start_day).zfill(3)
    end_day_text = str(end_day).zfill(3)
    base_name = f"{level_text}_DAY_{start_day_text}_{end_day_text}_FULL"

    return {
        "video": COMPILATION_VIDEO_ROOT / f"{base_name}.mp4",
        "thumbnail": COMPILATION_THUMBNAIL_ROOT / f"{base_name}.jpg",
    }


def backup_compilation_assets(level, start_day, end_day, delete_local=False):
    level_text = str(level).strip().upper()
    start_day_text = str(start_day).zfill(3)
    end_day_text = str(end_day).zfill(3)
    upload_key = f"{level_text}_DAY_{start_day_text}_{end_day_text}_FULL"
    paths = build_compilation_asset_paths(level_text, start_day_text, end_day_text)

    service = get_drive_service()
    root_folder_id = ensure_folder(service, ROOT_FOLDER_NAME)
    compilations_folder_id = ensure_folder(service, "compilations", parent_id=root_folder_id)
    level_folder_id = ensure_folder(service, level_text, parent_id=compilations_folder_id)
    range_folder_id = ensure_folder(
        service,
        f"DAY_{start_day_text}_{end_day_text}",
        parent_id=level_folder_id,
    )

    uploaded_files = {}
    for file_type, file_path in paths.items():
        uploaded_files[file_type] = upload_file(service, str(file_path), range_folder_id)

    update_uploaded_entry(
        upload_key,
        uploaded=False,
        drive_backed_up=True,
        drive_folder_id=range_folder_id,
        drive_video_file_id=uploaded_files["video"]["id"],
        drive_video_link=uploaded_files["video"].get("webViewLink"),
        drive_thumbnail_file_id=uploaded_files["thumbnail"]["id"],
        drive_thumbnail_link=uploaded_files["thumbnail"].get("webViewLink"),
    )

    deleted_files = {}
    if delete_local:
        for file_type, file_path in paths.items():
            deleted_files[file_type] = delete_local_file(str(file_path))

    return {
        "upload_key": upload_key,
        "drive_folder_id": range_folder_id,
        "uploaded_files": uploaded_files,
        "deleted_files": deleted_files,
    }
