# Legacy ePMP cron snapshot — 2026-09-29

This directory preserves source snapshots for legacy ePMP components found on CU01/Controlador during the AtmosLink provenance audit.

The `epmp_logs/` directory contains exact safe snapshots of the legacy RF polling scripts. The `epmp_monitor/` directory contains the sanitized current monitoring scripts and a safe `epmp.conf` snapshot; password files themselves are never included.

The active user crontab contains duplicate entries for `poll_epmp.sh` and `poll_epmp_agg.sh`. The audit records this condition but does not alter the crontab.

Credential-bearing ePMP monitor scripts were sanitized on 2026-09-29. Database and Telegram secrets now reside in separate protected files under `/home/carlos/.config/atmoslink/`, each mode `0600`. The repository stores only placeholder environment examples.

Original pre-sanitization source copies and their hashes remain in a protected local provenance directory outside Git. See `docs/provenance/CREDENTIAL_SANITIZATION_20260929.md` and `provenance/credential_sanitization_CU01_20260929.csv`.
