# DAILY TRACE — AtmosLink 3×2 — 2026-11-09

**Inspection cutoff:** 2026-11-09 23:53–23:55 America/Lima (UTC−05:00). **Method:** read-only terminal queries on authorized Controlador; read-only host/status query on authorized device labelled `rpi-cunacales`. No RF, PoE, VLAN, service, timer or database changes were performed. SQLite was opened with URI `mode=ro`; only aggregate statistics were extracted. This is a post-factorial trace; prospective Luisita windows are separate from the completed original 3×2 campaign.

## Evidence and operating state

Source database: Controlador's production CU01 SQLite, querying `scientific_campaign_6g_integrated`, `active_throughput_6g`, and `master_observations_multistation` (no DB export). Source for transitions/services: systemd journal and timer/service state.

**RF / scientific integrated:** 361 records dated 2026-11-09; 360 `LINK_OPERATIONAL_DUAL`, 1 `COLLECTION_ERROR`. Frequency/channel distribution: 6475 MHz / 40 MHz = 188, 6475 MHz / 20 MHz = 172, null frequency/bandwidth = 1 (collection error). Last integrated RF timestamp: **2026-11-09T22:55:01-05:00**. Mean nonzero DL/UL RSSI −77.72/−82.65 dBm; mean nonzero DL/UL SNR 22.27/18.86 dB. Weather dual matching: **353/361 = 97.78%**, 8 unmatched/other exceptions; matching does not independently establish trial eligibility.

**TCP (`active_throughput_6g`):** 180 tests on 2026-11-09, all status `OK`; 90 DL at mean 37.444 Mbps and 90 UL at mean 15.586 Mbps; combined mean 26.515 Mbps. First start 00:45:08, last start 23:45:23 local. Attribution to scientific treatment requires window-level QC, settling-period exclusion and linkage checks.

**Weather (`master_observations_multistation`):** CU01 1,358 records; last 23:51:27; mean temperature 18.49 °C, RH 62.47%, pressure 742.87 hPa, wind 0.26 m/s. SJ01 964 records; last 23:50:19; mean temperature 6.97 °C, RH 99.93%, pressure 666.34 hPa, wind 4.48 m/s. Remote synchronization reported `Status: OK` at 23:52:46 and service finished successfully at 23:52:47. The authorized device labelled `rpi-cunacales` answered host/status checks at 23:53:42 and showed no failed systemd units; its hostname was `rpi-cunacales`. Prior inventory associates this device label with the SJ01 Raspberry, but physical identity and local SJ01 weather records were not independently verified in this run. Do not treat its hostname alone as proof of location.

## Transitions and incidents

**Prospective Luisita P01_S05:** `WINDOW_INTENT` at 00:00:02; `TRIAL_ACK` 00:00:02; `CONFIRM_ACK` 00:00:55; `WINDOW_VERIFIED` **00:01:22** local, target **6475 MHz / 40 MHz**. The verified window specifies an analysis start 30 minutes after verification.

**Prospective Luisita P01_S06:** `WINDOW_INTENT` at 12:00:01; `TRIAL_ACK` 12:00:02; `CONFIRM_ACK` 12:00:54; `WINDOW_VERIFIED` **12:01:22** local, target **6475 MHz / 20 MHz**. Analysis start is 30 minutes after verification. These are operational confirmations, not final causal or statistical acceptance of exposures. Journal later reports `MONITORING` through 23:53 and service executions completed successfully. No confirmed new `SAFE_ABORT` or `executor_failure` was surfaced by the limited journal inspection; this is **not** an exhaustive negative certification. One RF `COLLECTION_ERROR` requires follow-up.

**Backup incident and recovery:** independent remote backup failed at **02:40:00** with `rateLimitExceeded`, `uploaded=False`, `verified=False`; service result `exit-code`. Backup recovery subsequently verified a single named archive at both primary and UNC destinations, with `RECOVERY COMPLETE 2/2` at **23:49:52**. This confirms dual verification of that archive, not reconciliation of every earlier pending backup. Scientific validation and weather sync timers were enabled; the latest observed remote-backup service result remained failed. Prospective and weather-watchdog timers were present; the scientific validation timer was scheduled next for 2026-11-10 00:05 local. No interventions or human changes were performed during inspection.

## Explicit scientific validation checkpoints

1. **Watermark advancement CONFIRMED:** `MAX(rf_timestamp_local)` in `scientific_campaign_6g_integrated` = **2026-11-09T22:55:01-05:00**, strictly later than **2026-09-15T23:36:42-05:00**.
2. **F6655_B20 new-row matching:** 0 new rows dated 2026-11-09; hence there is **no new-row test for today**. Historical 1,735 rows at 6655 MHz / 20 MHz, 1,705 dual-matched, **30 historical exceptions**. Previous new-row matching confirmations remain historical observations; continue checking each future new row for `cu01_weather_matched=1` **and** `sj01_weather_matched=1`. Do not claim 100% historical matching or close this checkpoint.
3. **Methodological decisions:** retain post-factorial and prospective records as distinct evidence streams; do not promote `WINDOW_VERIFIED` or TCP `OK` alone to valid experimental replicates; exclude settling and incident windows pending formal QC; preserve failed RF collection and backup-rate-limit events without imputing missing values.

**Limitations:** Daily cut is at inspection time, not an exhaustive midnight snapshot; source tables are live and later backfills may alter counts. Journal keyword review was limited; specialized executor logs were not exhaustively audited. No direct authenticated SJ01 SQLite inspection was completed. Evidence here is textual and aggregated, with no raw DB dumps, IPs, credentials, tokens or private host connection details.
