# Phase 2: External Webhook (cron-job.org) & Google OAuth 2.0

- **Date**: 06 Oct 2026
- **Status**: Failed due to GitHub Billing Quota Exhaustion (13 Oct 2026)
- **Objective**: Fix scheduling delays from Phase 1 and migrate to OAuth user authentication for Google Drive.

---

## 1. Architecture Overview

```
[cron-job.org] (Every 5 minutes, exact tick)
       │
       ▼ (HTTP POST with GitHub Token)
[GitHub REST API: repository_dispatch (collect / compile)]
       │
       ▼
[GitHub Actions Runner: .github/workflows/collect.yml]
       │
       ▼ (OAuth 2.0 User Token: GOOGLE_DRIVE_TOKEN_B64)
[Google Drive Storage: Raw/ & Final/]
```

---

## 2. Implementation Details

1. **Precision Triggering via External Cron**:
   - Registered two jobs on [cron-job.org](https://cron-job.org):
     - `collect`: Executed every 5 minutes 24/7 targeting `https://api.github.com/repos/vishall211/Delhi-Bus-Data-Automation/dispatches` with payload `{"event_type": "collect"}`.
     - `compile`: Executed daily at 23:55 IST with payload `{"event_type": "compile"}`.
2. **Workflow File Update**:
   - Replaced native `schedule` block with `repository_dispatch`:
     ```yaml
     on:
       repository_dispatch:
         types: [collect, compile]
       workflow_dispatch:
     ```
3. **Migration to Google Drive OAuth 2.0**:
   - Replaced Service Account authentication with user OAuth 2.0 flow:
     - Local authorization using `oauth_client.json` generating `token.json`.
     - Base64-encoded `token.json` uploaded to GitHub Secrets as `GOOGLE_DRIVE_TOKEN_B64`.
     - `drive.py` updated to decode `GOOGLE_DRIVE_TOKEN_B64` or fall back to local `token.json`.
   - Directly created date-wise subfolders in Google Drive: `Delhi Bus Data Automation/Raw/<DD Mon YYYY>/`.

---

## 3. The Quota Exhaustion Incident (13 Oct 2026)

On 13 Oct 2026, all automated data collection stopped abruptly.

### GitHub Actions Notification:
```text
GitHub: You have used 100% of the Actions minutes included for the vishall211 account.
Your plan includes 2,000 Actions minutes per month at no extra cost. 
You have used 100% so far this billing cycle.
(2,000 min used / 2,000 min included)
```

### Root Cause Analysis & Billing Math:
- **Execution Rate**:
  - 1 run every 5 minutes = 12 runs/hour.
  - $12 \times 24\text{ hours} = 288\text{ workflow runs per day}$.
  - $288 \times 30\text{ days} = 8,640\text{ workflow runs per month}$.
- **GitHub Runner Billing Policy**:
  - GitHub rounds **every runner execution up to the nearest whole minute**.
  - Even if `Collect.py` only took 15–20 seconds to execute, each run was billed as **1 full minute**.
- **The Breakdown**:
  $$\frac{2,000\text{ free monthly minutes}}{288\text{ minutes consumed per day}} \approx 6.94\text{ days}$$
  In less than 7 days, the entire monthly free allowance was burned, locking out the workflow until the next billing cycle.

---

## 4. Next Step
To eliminate per-minute billing entirely and achieve 24/7 autonomous collection, the project migrated to **Phase 3** (dedicated Oracle Cloud Infrastructure Always Free VM).

