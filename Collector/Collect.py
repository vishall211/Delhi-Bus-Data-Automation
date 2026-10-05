import os
import io
import pandas as pd

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from googleapiclient.http import MediaIoBaseDownload

from Collector.drive import (
    get_drive_service,
    find_folder,
    upload_csv
)


def list_files_in_folder(service, folder_id):

    query = (
        f"'{folder_id}' in parents "
        "and trashed = false"
    )

    results = service.files().list(
        q=query,
        spaces="drive",
        fields="files(id,name,mimeType)",
        orderBy="name"
    ).execute()

    return results.get("files", [])


def download_file(service, file_id, file_name):

    request = service.files().get_media(
        fileId=file_id
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

    return pd.read_csv(buffer)


def upload_or_replace(
    service,
    file_path,
    file_name,
    folder_id
):

    query = (
        f"name = '{file_name}' "
        f"and '{folder_id}' in parents "
        "and trashed = false"
    )

    results = service.files().list(
        q=query,
        spaces="drive",
        fields="files(id,name)"
    ).execute()

    existing = results.get("files", [])

    if existing:

        file_id = existing[0]["id"]

        from googleapiclient.http import MediaFileUpload

        media = MediaFileUpload(
            file_path,
            mimetype="text/csv",
            resumable=True
        )

        updated = service.files().update(
            fileId=file_id,
            media_body=media,
            fields="id,name"
        ).execute()

        return updated

    return upload_csv(
        service,
        file_path,
        file_name,
        folder_id
    )


def main():

    india = ZoneInfo("Asia/Kolkata")

    now = datetime.now(india)

    # Compile the previous completed Indian calendar day.
    target_date = now.date() - timedelta(days=1)

    date_folder_name = target_date.strftime(
        "%d %b %Y"
    )

    final_filename = (
        f"Delhi Bus - "
        f"{date_folder_name}.csv"
    )

    print("Connecting to Google Drive...")

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

    final_folder_id = find_folder(
        service,
        "Final",
        main_folder_id
    )

    date_folder_id = find_folder(
        service,
        date_folder_name,
        raw_folder_id
    )

    print(
        f"Reading snapshots for: "
        f"{date_folder_name}"
    )

    files = list_files_in_folder(
        service,
        date_folder_id
    )

    csv_files = [
        file
        for file in files
        if file["name"].endswith(".csv")
    ]

    print(
        "Snapshots found:",
        len(csv_files)
    )

    if not csv_files:

        print("No CSV snapshots found.")

        return

    dataframes = []

    for file in csv_files:

        print(
            "Reading:",
            file["name"]
        )

        df = download_file(
            service,
            file["id"],
            file["name"]
        )

        dataframes.append(df)

    combined = pd.concat(
        dataframes,
        ignore_index=True
    )

    records_before = len(combined)

    if (
        "entity_id" in combined.columns
        and "timestamp" in combined.columns
    ):

        combined = combined.drop_duplicates(
            subset=[
                "entity_id",
                "timestamp"
            ]
        )

        combined = combined.sort_values(
            [
                "entity_id",
                "timestamp"
            ]
        )

    else:

        combined = combined.drop_duplicates()

    records_after = len(combined)

    os.makedirs(
        "temp",
        exist_ok=True
    )

    local_path = os.path.join(
        "temp",
        final_filename
    )

    combined.to_csv(
        local_path,
        index=False
    )

    print()
    print("Compilation successful!")
    print("Date:", date_folder_name)
    print("Snapshots:", len(csv_files))
    print(
        "Records before deduplication:",
        records_before
    )
    print(
        "Final records:",
        records_after
    )
    print(
        "Duplicates removed:",
        records_before - records_after
    )

    print()
    print("Uploading final CSV...")

    uploaded = upload_or_replace(
        service,
        local_path,
        final_filename,
        final_folder_id
    )

    print()
    print("Final upload successful!")
    print(
        "Google Drive file:",
        uploaded["name"]
    )
    print(
        "File ID:",
        uploaded["id"]
    )


if __name__ == "__main__":
    main()