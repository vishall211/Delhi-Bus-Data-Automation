import os
import glob
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

RAW_FOLDER = os.path.join(
    PROJECT_DIR,
    "data",
    "raw"
)

FINAL_FOLDER = os.path.join(
    PROJECT_DIR,
    "data",
    "final"
)

os.makedirs(
    FINAL_FOLDER,
    exist_ok=True
)


# ============================================================
# TODAY'S DATA
# ============================================================

today = datetime.now(
    ZoneInfo("Asia/Kolkata")
).strftime("%Y-%m-%d")

today_folder = os.path.join(
    RAW_FOLDER,
    today
)


# ============================================================
# FIND SNAPSHOTS
# ============================================================

files = glob.glob(
    os.path.join(
        today_folder,
        "*.csv"
    )
)

print(f"Found {len(files)} snapshot files.")


if not files:

    print("No snapshot files found.")

    exit()


# ============================================================
# COMBINE SNAPSHOTS
# ============================================================

dataframes = []

for file in files:

    print(
        "Reading:",
        os.path.basename(file)
    )

    df = pd.read_csv(file)

    dataframes.append(df)


final_df = pd.concat(
    dataframes,
    ignore_index=True
)


# ============================================================
# REMOVE EXACT DUPLICATES
# ============================================================

before = len(final_df)

if "entity_id" in final_df.columns and "timestamp" in final_df.columns:

    final_df = final_df.drop_duplicates(

        subset=["entity_id", "timestamp"]

    )

else:

    final_df = final_df.drop_duplicates()

after = len(final_df)

duplicates_removed = before - after


# ============================================================
# SORT DATA
# ============================================================

if "entity_id" in final_df.columns and "timestamp" in final_df.columns:

    final_df = final_df.sort_values(

        by=["entity_id", "timestamp"]

    )

elif "timestamp" in final_df.columns:

    final_df = final_df.sort_values(

        by="timestamp"

    )


# ============================================================
# SAVE FINAL CSV
# ============================================================

filename = (
    f"Delhi Bus - "
    f"{datetime.strptime(today, '%Y-%m-%d').strftime('%d %b %Y')}.csv"
)

filepath = os.path.join(
    FINAL_FOLDER,
    filename
)

final_df.to_csv(
    filepath,
    index=False
)


# ============================================================
# RESULT
# ============================================================

print()
print("Compilation successful!")
print("Date:", today)
print("Snapshots:", len(files))

print("\n\nRecords before deduplication:", before)
print("Final unique records:", after)
print("Duplicate records removed:", duplicates_removed)
print("Saved:", filepath)