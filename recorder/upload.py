import os
import glob
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload

CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
REFRESH_TOKEN = os.environ.get('REFRESH_TOKEN')

FOLDER_ID = os.environ.get('FOLDER_ID')
STREAM_URL = os.environ.get('STREAM_URL', 'Unknown Stream')


def get_drive_service():
    creds = Credentials(
        token=None,
        refresh_token=REFRESH_TOKEN,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        token_uri="https://oauth2.googleapis.com/token"
    )
    return build('drive', 'v3', credentials=creds)


def clear_drive_folder_permanently(drive, folder_id):
    print("[INFO] Permanently deleting all files in folder...")

    query = f"'{folder_id}' in parents and trashed=false"

    page_token = None

    while True:
        results = drive.files().list(
            q=query,
            fields="nextPageToken, files(id, name)",
            pageToken=page_token
        ).execute()

        files = results.get('files', [])

        if not files:
            print("[INFO] No files found.")
            return

        for f in files:
            try:
                print(f"[DELETE] {f['name']} ({f['id']})")
                drive.files().delete(fileId=f['id']).execute()
            except Exception as e:
                print(f"[ERROR] Could not delete {f['name']}: {e}")

        page_token = results.get('nextPageToken')
        if not page_token:
            break

    print("[INFO] Folder fully cleared.")


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

        clear_drive_folder_permanently(drive, FOLDER_ID)

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
