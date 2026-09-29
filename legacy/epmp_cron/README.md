# Legacy ePMP cron snapshot — 2026-09-29

This directory preserves source snapshots for legacy ePMP components found on CU01/Controlador during the AtmosLink provenance audit.

The `epmp_logs/` directory contains exact snapshots of the legacy RF polling scripts. `poll_epmp.sh` and `poll_epmp_agg.sh` were retired from active cron execution on 2026-09-29 because they no longer contribute useful data to the current AtmosLink workflow. Their source and historical raw outputs remain preserved.

The `epmp_monitor/` directory contains the sanitized monitoring scripts and a safe `epmp.conf` snapshot; password files themselves are never included.

Credential-bearing ePMP monitor scripts were sanitized on 2026-09-29. Database and Telegram secrets reside in separate protected files under `/home/carlos/.config/atmoslink/`, each mode `0600`. The repository stores only placeholder environment examples.

Original pre-sanitization source copies and hashes remain in a protected local provenance directory outside Git. See the provenance documents under `docs/provenance/` and the manifests under `provenance/`.
