# Phase 3: Oracle Cloud Always Free VM & Native Linux Cron

- **Date**: 13 Oct 2026
- **Status**: Active & In Production
- **Objective**: Establish permanent, zero-cost, unmetered 24/7 automation with direct Google Drive syncing.

---

## 1. Architecture Overview

```
[Oracle Cloud Infrastructure (OCI) Always Free VM]
  │
  ├── Linux System cron daemon
  │     ├── Every 5 min: runs Collector/Collect.py
  │     └── Daily 23:55 IST: runs Compiler/Compile.py
  │
  ├── Local Persistent Python 3.12 Virtual Environment (.venv)
  │
  └── Google Drive Integration (OAuth 2.0 via token.json)
        │
        ▼ (Direct upload via Drive API v3)
  [Google Drive Storage: Raw/ & Final/]
```

---

## 2. Infrastructure Specifications

- **Cloud Provider**: Oracle Cloud Infrastructure (OCI)
- **Tenancy Home Region**: India West (`ap-mumbai-1`)
- **Instance Name**: `delhi-bus-collector`
- **Shape**: `VM.Standard.E2.1.Micro` (1 AMD OCPU, 1 GB RAM — **Always Free Eligible**)
- **Operating System**: Canonical Ubuntu 24.04 LTS
- **Public IP**: `161.118.164.81`
- **Default SSH User**: `ubuntu`
- **Boot Storage**: 47 GB (OCI Always Free tier includes up to 200 GB total block storage)
- **Monthly Cost**: **₹0.00 / $0.00** (Zero billing limits, zero runner minute caps)

---

## 3. Codebase Resiliency Updates

To ensure smooth headless execution from any directory on the VM:
1. **Directory-Independent Module Imports**:
   - `Collector/Collect.py` was updated to discover `COLLECTOR_DIR` and `PROJECT_DIR` dynamically and insert them into `sys.path`.
2. **Dynamic `temp/` Directory Resolution**:
   - Snapshots in `Collect.py` are now saved to `os.path.join(PROJECT_DIR, "temp")`, preventing rogue folders from being created when cron executes from different paths.
3. **Robust OAuth Token Discovery**:
   - `Collector/drive.py` now locates `token.json` relative to the repository root directory before falling back to working directory.
4. **Environment Isolation**:
   - Created `~/Delhi-Bus-Data-Automation/.env` on the VM containing `DELHI_API_KEY`.
   - Used persistent `.venv/` containing pinned requirements (`gtfs-realtime-bindings`, `google-api-python-client`, `pandas`, `requests`).

---

## 4. Production Crontab Configuration

Configured on the VM (`crontab -e` for user `ubuntu`):

```bash
# 1. Collect snapshots every 5 minutes
*/5 * * * * cd /home/ubuntu/Delhi-Bus-Data-Automation && export $(cat .env | xargs) && /home/ubuntu/Delhi-Bus-Data-Automation/.venv/bin/python Collector/Collect.py >> /home/ubuntu/collector.log 2>&1

# 2. Compile daily consolidated CSV at 23:55 IST (18:25 UTC server time)
25 18 * * * cd /home/ubuntu/Delhi-Bus-Data-Automation && export $(cat .env | xargs) && /home/ubuntu/Delhi-Bus-Data-Automation/.venv/bin/python Compiler/Compile.py >> /home/ubuntu/compiler.log 2>&1
```

---

## 5. Verification & Live Results

- **Live Test Execution**: 13 Oct 2026, 16:36:59 IST
  - Entities fetched: **4,192 live Delhi buses**
  - Snapshot generated: `snapshot_16-36-59.csv`
  - Upload status: Uploaded to `Google Drive/Delhi Bus Data Automation/Raw/13 Oct 2026/`
  - File ID: `1wFU46deyk2oMIjzTzz0_CKoWq4e_ctYa`
- **Operational Status**: Fully autonomous and persistent.

