import os
import pandas as pd
import requests

from google.transit import gtfs_realtime_pb2
from datetime import datetime
from zoneinfo import ZoneInfo

from drive import (
    get_drive_service,
    find_folder,
    get_or_create_folder,
    upload_csv
)


# ============================================================
# DELHI API
# ============================================================

API_KEY = os.environ["DELHI_API_KEY"]

URL = (
    "https://otd.delhi.gov.in/api/realtime/"
    f"VehiclePositions.pb?key={API_KEY}"
)


# ============================================================
# FETCH DATA
# ============================================================

print("Fetching Delhi bus data...")

response = requests.get(
    URL,
    timeout=30
)

response.raise_for_status()

feed = gtfs_realtime_pb2.FeedMessage()

feed.ParseFromString(
    response.content
)


# ============================================================
# EXTRACT VEHICLES
# ============================================================

rows = []

collected_at = datetime.now(
    ZoneInfo("Asia/Kolkata")
)

for entity in feed.entity:

    if not entity.HasField("vehicle"):
        continue

    vehicle = entity.vehicle

    row = {
        "entity_id": entity.id,
        "collected_at": collected_at.isoformat()
    }

    for field, value in vehicle.ListFields():

        name = field.name

        if field.message_type is not None:

            for sub_field, sub_value in value.ListFields():

                row[
                    f"{name}_{sub_field.name}"
                ] = str(sub_value)

        else:

            row[name] = value

    rows.append(row)


df = pd.DataFrame(rows)


# ============================================================
# SAVE TEMPORARY LOCAL FILE
# ============================================================

date_folder = collected_at.strftime(
    "%d %b %Y"
)

filename = collected_at.strftime(
    "snapshot_%H-%M-%S.csv"
)

os.makedirs(
    "temp",
    exist_ok=True
)

filepath = os.path.join(
    "temp",
    filename
)

df.to_csv(
    filepath,
    index=False
)


print()
print("Collection successful!")
print("Records:", len(df))
print("Local file:", filepath)


# ============================================================
# GOOGLE DRIVE
# ============================================================

print()
print("Connecting to Google Drive...")

service = get_drive_service()


# Find main folder
main_folder_id = find_folder(
    service,
    "Delhi Bus Data Automation"
)


# Find Raw folder
raw_folder_id = find_folder(
    service,
    "Raw",
    main_folder_id
)


# Create today's folder if required
daily_folder_id = get_or_create_folder(
    service,
    date_folder,
    raw_folder_id
)


# Upload CSV
uploaded = upload_csv(
    service,
    filepath,
    filename,
    daily_folder_id
)


print()
print("Upload successful!")
print("Google Drive file:", uploaded["name"])
print("File ID:", uploaded["id"])