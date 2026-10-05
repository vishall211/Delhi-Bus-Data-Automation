# Delhi Bus Data Automation

Automated pipeline that collects real-time GPS positions of Delhi buses using the [Delhi GTFS-Realtime API](https://otd.delhi.gov.in) and uploads snapshots to Google Drive.

## How It Works

The pipeline has two stages:

1. **Collector** — Fetches live vehicle positions from the Delhi transport API (GTFS-RT protobuf), parses them into a CSV snapshot, saves it locally, and uploads it to Google Drive.

2. **Compiler** — Reads all raw snapshots for the day, removes duplicate records, sorts by vehicle and timestamp, and produces a single consolidated CSV for the day.

A **GitHub Actions workflow** runs the Collector every 5 minutes automatically.

## Project Structure

```
Delhi Bus Data Automation/
├── .github/workflows/
│   └── collect.yml        # GitHub Actions workflow (runs every 5 min)
├── Collector/
│   ├── Collect.py         # Fetches API data → saves CSV → uploads to Drive
│   └── drive.py           # Google Drive auth, folder management, upload
├── Compiler/
│   └── Compile.py         # Combines daily snapshots → deduplicated final CSV
├── data/                  # Local data (git-ignored)
│   ├── raw/               # Raw snapshots organized by date
│   └── final/             # Compiled daily CSVs
├── temp/                  # Temporary files (git-ignored)
├── .gitignore
├── requirements.txt
└── README.md
```

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/vishall211/Delhi-Bus-Data-Automation.git
cd Delhi-Bus-Data-Automation
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set environment variables

The project requires two environment variables:

| Variable | Description |
|----------|-------------|
| `DELHI_API_KEY` | API key from [otd.delhi.gov.in](https://otd.delhi.gov.in) for accessing GTFS-RT feeds |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Full JSON content of a Google Cloud service account key (with Drive API access) |

For local development, export them in your shell:

```bash
export DELHI_API_KEY="your-api-key"
export GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account", ...}'
```

For GitHub Actions, add them as **repository secrets** with the same names.

### 5. Google Drive setup

Create this folder structure in Google Drive and **share it with the service account email**:

```
Delhi Bus Data Automation/
└── Raw/
```

The Collector will automatically create date-wise subfolders inside `Raw/`.

## Usage

### Collect a snapshot

```bash
cd Collector
python Collect.py
```

This will:
- Fetch current bus positions from the Delhi API
- Save a timestamped CSV to `temp/`
- Upload the CSV to Google Drive under `Raw/<date>/`

### Compile daily data

```bash
python Compiler/Compile.py
```

This will:
- Read all snapshots from `data/raw/<today>/`
- Remove duplicate records (by `entity_id` + `timestamp`)
- Save a consolidated CSV to `data/final/Delhi Bus - DD MMM YYYY.csv`

## Data Schema

Each snapshot contains these columns:

| Column | Description |
|--------|-------------|
| `entity_id` | Unique bus identifier (vehicle registration number) |
| `collected_at` | ISO timestamp of when the data was collected |
| `trip_trip_id` | GTFS trip ID |
| `trip_start_time` | Scheduled trip start time |
| `trip_start_date` | Trip date (YYYYMMDD) |
| `trip_schedule_relationship` | Schedule relationship (0 = scheduled, 1 = added) |
| `trip_route_id` | GTFS route ID |
| `position_latitude` | Bus latitude |
| `position_longitude` | Bus longitude |
| `position_speed` | Speed in m/s |
| `timestamp` | UNIX epoch timestamp from the bus GPS device |
| `vehicle_id` | Vehicle identifier |
| `vehicle_label` | Vehicle display label |

## GitHub Actions

The workflow (`.github/workflows/collect.yml`) runs every 5 minutes via cron. It uses repository secrets `DELHI_API_KEY` and `GOOGLE_SERVICE_ACCOUNT_JSON` to authenticate with the Delhi API and Google Drive respectively.

You can also trigger it manually from the **Actions** tab on GitHub using the `workflow_dispatch` trigger.

## License

This project is for personal/educational use.

