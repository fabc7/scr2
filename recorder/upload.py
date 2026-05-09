import os
import glob

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request


# === ENV VARIABLES ===
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
REFRESH_TOKEN = os.environ.get('REFRESH_TOKEN')

FOLDER_ID = os.environ.get('FOLDER_ID')
STREAM_URL = os.environ.get('STREAM_URL', 'Unknown Stream')

# IMPORTANTE: scopes necesarios para Drive
SCOPES = ['https://www.googleapis.com/auth/drive.file']


def get_drive_service():
    if not all([CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN]):
        raise ValueError("Faltan variables de entorno de autenticación (CLIENT_ID, CLIENT_SECRET o REFRESH_TOKEN)")

    creds = Credentials(
        token=None,
        refresh_token=REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        scopes=SCOPES
    )

    # Refrescar el access token explícitamente
    creds.refresh(Request())

    return build('drive', 'v3', credentials=creds)


def upload_latest_video():
    files = glob.glob('**/*.mkv', recursive=True)

    if not files:
        print("[ERROR] No MKV files found to upload.")
        return

    files.sort(key=os.path.getmtime)
    video_file = files[-1]

    print(f"[INFO] Video found for upload: {video_file}")

    base_name = os.path.basename(video_file)
    name_without_ext = os.path.splitext(base_name)[0]
    file_title = name_without_ext.replace('_', ' ')

    try:
        drive = get_drive_service()

        file_metadata = {
            'name': file_title,
            'parents': [FOLDER_ID]
        }

        print(f"[INFO] Uploading to Google Drive as '{file_title}'...")

        media = MediaFileUpload(video_file, resumable=True)

        request = drive.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Upload Progress: {int(status.progress() * 100)}%")

        print(f"\n[SUCCESS] Upload complete! File ID: {response.get('id')}")

    except Exception as e:
        print(f"[ERROR] Drive Upload failed: {e}")


if __name__ == '__main__':
    upload_latest_video()
