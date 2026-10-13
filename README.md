# Delhi Bus Data Automation

Automated pipeline that collects real-time GPS positions of Delhi buses using the [Delhi GTFS-Realtime API](https://otd.delhi.gov.in) and uploads snapshots to Google Drive.

The pipeline runs 24/7 on an **Oracle Cloud Infrastructure (OCI) Always Free VM** using Linux `cron`, with zero recurring costs.

*(For detailed architectural decision records and the evolution history from GitHub Actions to Oracle VM, see [`progress/ARCHITECTURE_LOG.md`](progress/ARCHITECTURE_LOG.md)).*

## How It Works

The pipeline consists of two stages:

1. **Collector** — Fetches live vehicle positions from the Delhi transport API (GTFS-RT protobuf), parses them into a CSV snapshot, saves it temporarily, and uploads it to Google Drive under `Delhi Bus Data Automation/Raw/<DD Mon YYYY>/`.
2. **Compiler** — Reads all raw snapshots for today directly from Google Drive, removes duplicate records (`entity_id` + `timestamp`), sorts the consolidated dataset, and uploads a daily final CSV to Google Drive under `Delhi Bus Data Automation/Final/Delhi Bus - <DD Mon YYYY>.csv`.

Automation runs automatically 24/7 on an Oracle Cloud Linux instance via `cron` (every 5 minutes for collection, and 23:55 IST for compilation).

---

## Project Structure

```
Delhi Bus Data Automation/
├── progress/
│   ├── 01_Phase1_GitHub_Actions_Cron_2026-10-05.md # Initial GitHub Actions + Service Account setup
│   ├── 02_Phase2_External_Cron_OAuth_2026-10-06.md # cron-job.org dispatch & quota incident analysis
│   ├── 03_Phase3_Oracle_Cloud_VM_2026-10-13.md     # Current Oracle Cloud VM production deployment
│   └── SUMMARY_PROGRESS.md                         # Master summary covering all evolution milestones
├── .github/workflows/
│   └── collect.yml        # GitHub Actions workflow (legacy / fallback)
├── Collector/
│   ├── Collect.py         # Fetches API data → saves CSV → uploads to Drive
│   └── drive.py           # Google Drive OAuth auth, folder management, upload
├── Compiler/
│   └── Compile.py         # Downloads daily snapshots from Drive → deduplicated final CSV
├── data/                  # Local data directory (git-ignored)
├── temp/                  # Temporary snapshot directory (git-ignored)
├── temp_compile/          # Temporary compilation directory (git-ignored)
├── .gitignore
├── requirements.txt
└── README.md
```

---

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

### 4. Authentication & Environment Variables

The project uses OAuth 2.0 to access Google Drive and an API key from Delhi Open Transit Data.

| Variable | Description |
|----------|-------------|
| `DELHI_API_KEY` | API key from [otd.delhi.gov.in](https://otd.delhi.gov.in) for accessing GTFS-RT feeds |
| `GOOGLE_DRIVE_TOKEN_B64` | Base64-encoded string of the OAuth `token.json` file (used for GitHub Actions / headless runs) |

#### Local Development
For local runs, place your generated `token.json` in the project root (it is git-ignored):
```bash
export DELHI_API_KEY="your-api-key"
```
*(If `GOOGLE_DRIVE_TOKEN_B64` is not set, `drive.py` automatically falls back to reading `token.json` from the root directory).*

#### GitHub Actions
For automated runs on GitHub Actions, add these as **Repository Secrets** in **Settings → Secrets and variables → Actions**:
1. `DELHI_API_KEY`: Your Delhi Open Transit API key.
2. `GOOGLE_DRIVE_TOKEN_B64`: Base64-encoded content of your `token.json`. To generate this string locally:
   ```bash
   base64 -i token.json | tr -d '\n'
   ```

### 5. Google Drive Folder Structure

Ensure the following folder structure exists in your Google Drive:

```
Delhi Bus Data Automation/
├── Raw/
└── Final/
```

- The Collector will automatically create date-wise subfolders inside `Raw/` (e.g. `Raw/08 Oct 2026/`).
- The Compiler will upload the consolidated daily file to `Final/`.

---

## Usage

### Run Collector Locally

```bash
python Collector/Collect.py
```

This will:
- Fetch current bus positions from the Delhi API
- Save a timestamped CSV to `temp/`
- Upload the CSV to Google Drive under `Delhi Bus Data Automation/Raw/<date>/`

### Run Compiler Locally

```bash
python Compiler/Compile.py
```

This will:
- Query Google Drive for all snapshots in `Delhi Bus Data Automation/Raw/<today>/`
- Download and combine all snapshot records
- Remove duplicate records (by `entity_id` + `timestamp`)
- Upload the consolidated file to `Delhi Bus Data Automation/Final/Delhi Bus - <date>.csv`

---

## Data Schema

Each snapshot contains the following columns:

| Column | Description |
|--------|-------------|
| `entity_id` | Unique bus identifier (vehicle registration number) |
| `trip_trip_id` | GTFS trip ID |
| `trip_start_time` | Scheduled trip start time |
| `trip_start_date` | Trip date (`YYYYMMDD`) |
| `trip_schedule_relationship` | Schedule relationship (`0` = scheduled, `1` = added) |
| `trip_route_id` | GTFS route ID |
| `position_latitude` | Bus latitude |
| `position_longitude` | Bus longitude |
| `position_speed` | Speed in m/s |
| `timestamp` | UNIX epoch timestamp from the bus GPS device |
| `vehicle_id` | Vehicle identifier |
| `vehicle_label` | Vehicle display label |

---

## GitHub Actions & Automated Scheduling

The workflow ([`.github/workflows/collect.yml`](.github/workflows/collect.yml)) supports:

1. **`workflow_dispatch`**: Trigger data collection manually anytime from GitHub's **Actions** tab.
2. **`repository_dispatch`**: Triggered externally via GitHub API webhooks:
   - Event `collect`: Runs `Collector/Collect.py` (e.g. every 5 minutes from [cron-job.org](https://cron-job.org)).
   - Event `compile`: Runs `Compiler/Compile.py` (e.g. nightly at 23:55 IST).

---

## License

This project is for personal/educational use.
