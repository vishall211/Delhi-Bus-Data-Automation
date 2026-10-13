# Phase 1: GitHub Actions & Google Cloud Service Account

- **Date**: 05 Oct 2026
- **Status**: Retired / Superseded
- **Objective**: Automate real-time Delhi bus GPS collection every 5 minutes and store snapshots in Google Drive.

---

## 1. Architecture Overview

```
[Delhi OTD API]
       │
       ▼ (Every 5 minutes via GitHub Actions schedule)
[GitHub-Hosted Runner (ubuntu-latest)]
       │
       ▼ (Service Account Auth)
[Google Drive Storage: Raw/ & Final/]
```

---

## 2. Implementation Details

1. **Trigger Mechanism**:
   - Native GitHub Actions workflow schedule:
     ```yaml
     on:
       schedule:
         - cron: "*/5 * * * *"
       workflow_dispatch:
     ```
2. **Execution Environment**:
   - GitHub-hosted runner (`ubuntu-latest`).
   - Virtual environment built dynamically for every run via `actions/setup-python@v5` installing `requirements.txt`.
3. **Data Fetching & Parsing**:
   - `Collector/Collect.py` fetched GTFS-RT protobuf data from `https://otd.delhi.gov.in/api/realtime/VehiclePositions.pb`.
   - Converted protobuf entities to Pandas DataFrame.
   - Saved temporary CSV snapshots locally in `data/raw/<today>/`.
4. **Google Drive Integration**:
   - Used Google Cloud Service Account credentials (`GOOGLE_SERVICE_ACCOUNT_JSON`).
   - Uploaded snapshots into Google Drive under `Delhi Bus Data Automation/Raw/`.

---

## 3. Problems & Limitations Encountered

1. **Severe Schedule Jitter & Delays**:
   - GitHub Actions' built-in cron scheduler is notoriously unreliable during high-traffic intervals.
   - 5-minute cron jobs frequently experienced delays of 15 to 45 minutes, causing significant gaps in the time-series GPS data.
2. **Drive Permissions & Storage Constraints**:
   - Google Service Accounts have their own distinct storage quota rather than utilizing standard personal Google Drive space unless carefully mapped through shared drives or specific folder permissions.
3. **High Overhead Per Run**:
   - Booting up a complete Ubuntu runner, installing Python, and running `pip install` every 5 minutes was resource-heavy and slow (~1 to 2 minutes per cycle for ~10 seconds of actual API fetching).

---

## 4. Next Step
To resolve schedule jitter and permission issues, the architecture was shifted to **Phase 2** (external webhook trigger via `cron-job.org` and Google OAuth 2.0 user credentials).

