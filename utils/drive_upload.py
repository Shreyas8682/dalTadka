import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Resolve path to service account credentials
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), "..", "dalTadka-f8dc74bf3c4c.json")
SCOPES = ['https://www.googleapis.com/auth/drive']

if not os.path.exists(SERVICE_ACCOUNT_FILE):
    raise FileNotFoundError(f"❌ Service account file not found at: {SERVICE_ACCOUNT_FILE}")

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
drive_service = build('drive', 'v3', credentials=credentials)

def upload_to_drive(filepath, filename, folder_id=None):
    file_metadata = {'name': filename}
    if folder_id:
        file_metadata['parents'] = [folder_id]

    media = MediaFileUpload(filepath, resumable=True)
    uploaded_file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    file_id = uploaded_file.get('id')

    # ✅ Set permissions to make the file PUBLIC
    drive_service.permissions().create(
        fileId=file_id,
        body={
            'type': 'anyone',
            'role': 'reader'
        },
        fields='id'
    ).execute()

    # ✅ Return directly usable PUBLIC IMAGE URL
    public_url = f"https://drive.google.com/uc?export=view&id={file_id}"
    return {
        "url": public_url,
        "file_id": file_id
    }

def delete_file_from_drive(file_id):
    try:
        drive_service.files().delete(fileId=file_id).execute()
        return True
    except Exception as e:
        print(f"❌ Error deleting file from Drive: {file_id} - {e}")
        return False
