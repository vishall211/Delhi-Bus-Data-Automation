import os
import json
import io

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload


# ============================================================
# GOOGLE DRIVE AUTHENTICATION
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/drive"
]


def get_drive_service():

    credentials_json = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]

    credentials = service_account.Credentials.from_service_account_info(
        json.loads(credentials_json),
        scopes=SCOPES
    )

    return build(
        "drive",
        "v3",
        credentials=credentials
    )


# ============================================================
# FIND FOLDER
# ============================================================

def find_folder(service, folder_name, parent_id=None):

    query = (
        "name = '{}' "
        "and mimeType = 'application/vnd.google-apps.folder' "
        "and trashed = false"
    ).format(folder_name)

    if parent_id:
        query += f" and '{parent_id}' in parents"

    results = service.files().list(
        q=query,
        spaces="drive",
        fields="files(id, name)",
        pageSize=10
    ).execute()

    files = results.get("files", [])

    if not files:
        raise Exception(
            f"Google Drive folder not found: {folder_name}"
        )

    return files[0]["id"]


# ============================================================
# CREATE FOLDER
# ============================================================

def create_folder(service, folder_name, parent_id):

    metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id]
    }

    folder = service.files().create(
        body=metadata,
        fields="id"
    ).execute()

    return folder["id"]


# ============================================================
# GET OR CREATE FOLDER
# ============================================================

def get_or_create_folder(
    service,
    folder_name,
    parent_id
):

    try:

        return find_folder(
            service,
            folder_name,
            parent_id
        )

    except Exception:

        return create_folder(
            service,
            folder_name,
            parent_id
        )


# ============================================================
# UPLOAD CSV
# ============================================================

def upload_csv(
    service,
    file_path,
    file_name,
    folder_id
):

    with open(
        file_path,
        "rb"
    ) as file:

        media = MediaIoBaseUpload(
            io.BytesIO(file.read()),
            mimetype="text/csv",
            resumable=True
        )

    metadata = {
        "name": file_name,
        "parents": [folder_id]
    }

    uploaded = service.files().create(
        body=metadata,
        media_body=media,
        fields="id,name"
    ).execute()

    return uploaded