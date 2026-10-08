import os
import sys
import io
import pandas as pd

from datetime import datetime
from zoneinfo import ZoneInfo

from googleapiclient.http import MediaIoBaseDownload

# Allow importing Collector/drive.py
PROJECT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.insert(
    0,
    os.path.join(PROJECT_DIR, "Collector")
)

from drive import (
    get_drive_service,
    find_folder,
    upload_csv
)


# ============================================================
# TODAY
# ============================================================

today = datetime.now(
    ZoneInfo("Asia/Kolkata")
)

date_folder = today.strftime("%d %b %Y")

print("Compiling data for:", date_folder)


# ============================================================
# GOOGLE DRIVE
# ============================================================

service = get_drive_service()

main_folder_id = find_folder(
    service,
    "Delhi Bus Data Automation"
)

raw_folder_id = find_folder(
    service,
    "Raw",
    main_folder_id
)

today_folder_id = find_folder(
    service,
    date_folder,
    raw_folder_id
)

final_folder_id = find_folder(
    service,
    "Final",
    main_folder_id
)


# ============================================================
# FIND RAW CSV FILES
# ============================================================

query = (
    f"'{today_folder_id}' in parents "
    "and mimeType = 'text/csv' "
    "and trashed = false"
)

files = []
page_token = None

while True:
    results = service.files().list(
        q=query,
        spaces="drive",
        fields="nextPageToken, files(id,name)",
        pageSize=1000,
        pageToken=page_token
    ).execute()

    files.extend(results.get("files", []))
    page_token = results.get("nextPageToken")

    if not page_token:
        break

print("Found", len(files), "snapshot files.")


if not files:
    print("No snapshot files found.")
    sys.exit(0)


# ============================================================
# DOWNLOAD AND COMBINE
# ============================================================

dataframes = []

temp_folder = os.path.join(
    PROJECT_DIR,
    "temp_compile"
)

os.makedirs(
    temp_folder,
    exist_ok=True
)


for file in files:

    print("Downloading:", file["name"])

    request = service.files().get_media(
        fileId=file["id"]
    )

    buffer = io.BytesIO()

    downloader = MediaIoBaseDownload(
        buffer,
        request
    )

    done = False

    while not done:

        _, done = downloader.next_chunk()

    buffer.seek(0)

    df = pd.read_csv(buffer)

    dataframes.append(df)


# ============================================================
# COMBINE
# ============================================================

final_df = pd.concat(
    dataframes,
    ignore_index=True
)


# ============================================================
# REMOVE DUPLICATES
# ============================================================

before = len(final_df)

if (
    "entity_id" in final_df.columns
    and
    "timestamp" in final_df.columns
):

    final_df = final_df.drop_duplicates(
        subset=[
            "entity_id",
            "timestamp"
        ]
    )

else:

    final_df = final_df.drop_duplicates()


after = len(final_df)


# ============================================================
# SORT
# ============================================================

if (
    "entity_id" in final_df.columns
    and
    "timestamp" in final_df.columns
):

    final_df = final_df.sort_values(
        by=[
            "entity_id",
            "timestamp"
        ]
    )

elif "timestamp" in final_df.columns:

    final_df = final_df.sort_values(
        by="timestamp"
    )


# ============================================================
# SAVE FINAL FILE
# ============================================================

filename = (
    f"Delhi Bus - {date_folder}.csv"
)

filepath = os.path.join(
    temp_folder,
    filename
)

final_df.to_csv(
    filepath,
    index=False
)


# ============================================================
# UPLOAD TO GOOGLE DRIVE
# ============================================================

print("Uploading final CSV to Google Drive...")

uploaded = upload_csv(
    service,
    filepath,
    filename,
    final_folder_id
)


# ============================================================
# RESULT
# ============================================================

print()
print("Compilation successful!")
print("Snapshots:", len(files))
print("Records before deduplication:", before)
print("Final unique records:", after)
print("Duplicates removed:", before - after)
print("Final file:", uploaded["name"])