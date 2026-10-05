import os
import io
import requests
import pandas as pd

from datetime import datetime
from zoneinfo import ZoneInfo

from google.protobuf.json_format import MessageToDict
from google.transit import gtfs_realtime_pb2

from drive import (
    get_drive_service,
    find_folder,
    get_or_create_folder,
    upload_csv
)


API_URL = "https://otd.delhi.gov.in/api/realtime/VehiclePositions.pb"


def collect_vehicle_data(api_key):

    print("Fetching Delhi bus realtime data...")

    response = requests.get(
        API_URL,
        params={"key": api_key},
        timeout=60
    )

    response.raise_for_status()

    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(response.content)

    print(
        "Entities received:",
        len(feed.entity)
    )

    records = []

    for entity in feed.entity:

        if not entity.HasField("vehicle"):
            continue

        vehicle = entity.vehicle

        trip = vehicle.trip
        position = vehicle.position
        vehicle_descriptor = vehicle.vehicle

        records.append({
            "entity_id": entity.id,

            "trip_trip_id": (
                trip.trip_id
                if trip.HasField("trip_id")
                else ""
            ),

            "trip_start_time": (
                trip.start_time
                if trip.HasField("start_time")
                else ""
            ),

            "trip_start_date": (
                trip.start_date
                if trip.HasField("start_date")
                else ""
            ),

            "trip_schedule_relationship": (
                str(trip.schedule_relationship)
                if trip.HasField("schedule_relationship")
                else ""
            ),

            "trip_route_id": (
                trip.route_id
                if trip.HasField("route_id")
                else ""
            ),

            "position_latitude": (
                position.latitude
                if position.HasField("latitude")
                else ""
            ),

            "position_longitude": (
                position.longitude
                if position.HasField("longitude")
                else ""
            ),

            "position_speed": (
                position.speed
                if position.HasField("speed")
                else ""
            ),

            "timestamp": (
                vehicle.timestamp
                if vehicle.HasField("timestamp")
                else ""
            ),

            "vehicle_id": (
                vehicle_descriptor.id
                if vehicle_descriptor.HasField("id")
                else ""
            ),

            "vehicle_label": (
                vehicle_descriptor.label
                if vehicle_descriptor.HasField("label")
                else ""
            )
        })

    return pd.DataFrame(records)


def main():

    api_key = os.environ.get("DELHI_API_KEY")

    if not api_key:
        raise Exception(
            "DELHI_API_KEY environment variable is missing."
        )

    india = ZoneInfo("Asia/Kolkata")
    now = datetime.now(india)

    date_folder_name = now.strftime("%d %b %Y")
    snapshot_filename = (
        f"snapshot_{now.strftime('%H-%M-%S')}.csv"
    )

    # --------------------------------------------------
    # Collect data
    # --------------------------------------------------

    df = collect_vehicle_data(api_key)

    if df.empty:
        print("No vehicle data received.")

        return

    print(
        "Records collected:",
        len(df)
    )

    # --------------------------------------------------
    # Save temporary CSV
    # --------------------------------------------------

    os.makedirs(
        "temp",
        exist_ok=True
    )

    local_path = os.path.join(
        "temp",
        snapshot_filename
    )

    df.to_csv(
        local_path,
        index=False
    )

    print(
        "Temporary CSV created:",
        local_path
    )

    # --------------------------------------------------
    # Connect to Google Drive
    # --------------------------------------------------

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

    # --------------------------------------------------
    # Get/create today's date folder
    # --------------------------------------------------

    date_folder_id = get_or_create_folder(
        service,
        date_folder_name,
        raw_folder_id
    )

    # --------------------------------------------------
    # Upload snapshot
    # --------------------------------------------------

    uploaded = upload_csv(
        service,
        local_path,
        snapshot_filename,
        date_folder_id
    )

    print()
    print("Collection successful!")
    print("Date:", date_folder_name)
    print("Records:", len(df))
    print("Saved:", snapshot_filename)
    print("Google Drive file ID:", uploaded["id"])


if __name__ == "__main__":
    main()