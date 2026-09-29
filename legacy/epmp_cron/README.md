# Legacy ePMP cron snapshot — 2026-09-29

This directory preserves exact source snapshots for legacy ePMP shell components found on CU01/Controlador during the AtmosLink provenance audit.

Captured exact scripts:
- `/home/carlos/epmp_logs/ap_snr_agg.sh`
- `/home/carlos/epmp_logs/housekeeping.sh`
- `/home/carlos/epmp_logs/poll_epmp.sh`
- `/home/carlos/epmp_logs/poll_epmp_agg.sh`
- `/home/carlos/epmp_logs/watchdog_poll.sh`
- `/home/carlos/epmp_monitor/bin/alert_epmp.sh`

The active user crontab contains duplicate entries for `poll_epmp.sh` and `poll_epmp_agg.sh`; this audit records the condition but does not alter the crontab.

`/home/carlos/epmp_monitor/bin/auto_csv_pipeline.sh` is active in cron but is deliberately not copied verbatim into Git because the deployed file contains literal database-password material. `alertas_automaticas.py` is also withheld from normal Git because the audit detected a possible literal token. Their production hashes remain recorded in `provenance/legacy_cron_CU01_20260929.csv`.

Those secret-bearing components require a separate credential-extraction/refactor before source versioning. No credential value is recorded here.
