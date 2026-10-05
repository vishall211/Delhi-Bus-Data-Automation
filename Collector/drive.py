import os
import json
import io

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload


SCOPES = [
    "https://www.googleapis.com/auth/drive"
]


def get_drive_service():

    token_json = os.environ.get("GOOGLE_DRIVE_TOKEN_JSON")

    if token_json:
        credentials = Credentials.from_authorized_user_info(
            json.loads(token_json),
            SCOPES
        )
    else:
        credentials = Credentials.from_authorized_user_file(
            "token.json",
            SCOPES
        )

    return build(
        "drive",
        "v3",
        credentials=credentials
    )


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


def get_or_create_folder(service, folder_name, parent_id):

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


def upload_csv(service, file_path, file_name, folder_id):

    with open(file_path, "rb") as file:

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