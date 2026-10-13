# Delhi Bus Data Automation: Project Evolution & Architectural Summary

This master document provides a comprehensive, unified history of all architecture phases, decisions, incident post-mortems, and deployment steps for the **Delhi Bus Data Automation** pipeline.

---

## Executive Summary

| Phase | Date | Trigger Mechanism | Compute Platform | Storage Destination | Outcome / Status |
|---|---|---|---|---|---|
| **Phase 1** | **05 Oct 2026** | GitHub Actions schedule (`cron: "*/5 * * * *"`) | GitHub-hosted Runner (`ubuntu-latest`) | Google Drive via Service Account | Retired due to severe cron delays (15–45 min) and permissions friction. |
| **Phase 2** | **06 Oct 2026** | External Webhook ([cron-job.org](https://cron-job.org)) → GitHub `repository_dispatch` | GitHub-hosted Runner (`ubuntu-latest`) | Google Drive via OAuth 2.0 user tokens | Failed on **13 Oct 2026** after exhausting all 2,000 GitHub free minutes in 7 days. |
| **Phase 3** | **13 Oct 2026** | Native Linux System `cron` daemon | **Oracle Cloud Infrastructure (OCI)** Always Free VM (`VM.Standard.E2.1.Micro`) | Google Drive via OAuth 2.0 (`Raw/` & `Final/`) | **Active & In Production**. 100% free forever with zero runtime minute limits. |

---

## Detailed Chronology of Phases

```
   ┌─────────────────────────────────────────────────────────┐
   │ 05 Oct 2026: Phase 1                                    │
   │ GitHub Actions Built-in Cron + Google Service Account   │
   └───────────────────────────┬─────────────────────────────┘
                               │
               Issue: Cron jitter & delay (15-45m)
                               ▼
   ┌─────────────────────────────────────────────────────────┐
   │ 06 Oct 2026: Phase 2                                    │
   │ cron-job.org Webhook Dispatch + Google OAuth 2.0        │
   └───────────────────────────┬─────────────────────────────┘
                               │
       Incident: 2,000 monthly runner minutes burned in 7 days
                               ▼
   ┌─────────────────────────────────────────────────────────┐
   │ 13 Oct 2026: Phase 3 (Current Production)               │
   │ Dedicated Oracle Cloud Always Free VM + Linux Cron      │
   └─────────────────────────────────────────────────────────┘
```

---

### Phase 1: Built-in GitHub Actions & Service Account (05 Oct 2026)
*Full details: [`progress/01_Phase1_GitHub_Actions_Cron_2026-10-05.md`](01_Phase1_GitHub_Actions_Cron_2026-10-05.md)*

- **Original Goal**: Continuously capture real-time GPS locations of Delhi transport buses from the open transit data feed (`https://otd.delhi.gov.in/api/realtime/VehiclePositions.pb`).
- **Design**:
  - Run `.github/workflows/collect.yml` on a 5-minute cron.
  - Store credentials as `GOOGLE_SERVICE_ACCOUNT_JSON` in GitHub Secrets.
- **Failures Identified**:
  - GitHub Actions runs cron workflows with low priority on a shared pool, causing delays up to 45 minutes between runs.
  - Service accounts required awkward folder sharing and had quota isolation issues.

---

### Phase 2: External Cron & OAuth 2.0 Migration (06 Oct 2026)
*Full details: [`progress/02_Phase2_External_Cron_OAuth_2026-10-06.md`](02_Phase2_External_Cron_OAuth_2026-10-06.md)*

- **Modifications**:
  - Moved trigger to [cron-job.org](https://cron-job.org) hitting GitHub's `repository_dispatch` webhook to eliminate cron latency.
  - Migrated authentication to OAuth 2.0 user credentials via base64 secret `GOOGLE_DRIVE_TOKEN_B64`.
- **The Quota Breakdown (13 Oct 2026 Incident)**:
  - GitHub billed 1 minute per run, regardless of actual duration (15–20s):
    $$\frac{60\text{ min}}{5\text{ min}} = 12\text{ runs/hr} \times 24\text{ hrs} = 288\text{ min/day} \times 30\text{ days} = 8,640\text{ min/month}$$
  - The monthly free allowance of 2,000 minutes was completely drained in **under 7 days** ($\frac{2000}{288} \approx 6.94\text{ days}$), shutting down the pipeline.

---

### Phase 3: Oracle Cloud Always Free VM & Native Cron (13 Oct 2026 - Present)
*Full details: [`progress/03_Phase3_Oracle_Cloud_VM_2026-10-13.md`](03_Phase3_Oracle_Cloud_VM_2026-10-13.md)*

- **Why Chosen**:
  - Oracle Cloud Infrastructure provides an **Always Free Tier** that does not expire after a trial period.
  - Running a dedicated VM removes all minute-based billing caps.
- **VM Specifications**:
  - **Instance**: `delhi-bus-collector`
  - **Shape**: `VM.Standard.E2.1.Micro` (1 AMD OCPU, 1 GB RAM, Always Free)
  - **OS**: Canonical Ubuntu 24.04 LTS
  - **Region**: India West (`ap-mumbai-1`)
  - **IP**: `161.118.164.81`
- **Code Refactoring & Hardening**:
  - Added dynamic path discovery to `Collector/Collect.py` and `Collector/drive.py` so scripts run cleanly regardless of the directory from which they are executed.
  - Added `nextPageToken` pagination in `Compiler/Compile.py` for guaranteed collection completeness.
- **Active Cron Schedule on VM**:
  - `*/5 * * * *` — Snapshot collection every 5 minutes.
  - `25 18 * * *` (23:55 IST) — Daily compilation and deduplication.
- **Verification**:
  - Successfully verified on 13 Oct 2026 with 4,192 bus entities saved and uploaded to Google Drive.

---

## Directory Reference in `progress/`

- [`progress/01_Phase1_GitHub_Actions_Cron_2026-10-05.md`](01_Phase1_GitHub_Actions_Cron_2026-10-05.md): Phase 1 setup and limitations.
- [`progress/02_Phase2_External_Cron_OAuth_2026-10-06.md`](02_Phase2_External_Cron_OAuth_2026-10-06.md): Phase 2 setup and the quota incident post-mortem.
- [`progress/03_Phase3_Oracle_Cloud_VM_2026-10-13.md`](03_Phase3_Oracle_Cloud_VM_2026-10-13.md): Phase 3 Oracle Cloud VM specifications and setup.
- [`progress/SUMMARY_PROGRESS.md`](SUMMARY_PROGRESS.md): Master summary covering all evolution milestones.

