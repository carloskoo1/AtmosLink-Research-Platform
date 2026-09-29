# CU01 performance audit — 2026-09-29

## Scope

Read-only audit of CPU, RAM, swap, disk I/O, systemd services, dashboard request behavior, SQLite access patterns, scheduler task cadence and legacy processes on Controlador/CU01. No scientific database rows were modified by the audit.

## Host baseline

- CPU: Intel Core i5-5200U, 2 physical cores / 4 logical CPUs.
- RAM: 7.7 GiB.
- Root filesystem: 468 GiB, approximately 16% used.
- Initial load average observed: 1.26 / 1.26 / 1.28.
- Swap in use during the audit: approximately 0.8–1.0 GiB.

## Dominant finding: full multistation rebuild after every remote sync

`atmoslink-remote-sync.timer` starts approximately every 120 seconds. The service synchronizes only the new SJ01 rows, normally 1–2 rows per run, but its `ExecStartPost` then executes:

`python -u -m weather_station.sync.build_multistation_master`

The builder performs a full-table pandas rebuild: it reads the complete master, station observations, ERA5 and NASA tables, reconstructs the multistation dataset, rewrites the SQL table atomically, and rewrites the full CSV.

At the time of the audit the multistation table contained about 169.7k rows.

Observed service runs consumed roughly 28–31 CPU seconds and reached approximately 1.2–1.4 GiB memory peak. One directly measured builder invocation used:

- elapsed: 11.83 s
- CPU: 10.16 s
- peak RSS: 1237 MiB
- characters read: 181.4 MiB
- characters written: 353.66 MiB
- block write_bytes: 353.72 MiB

The exact runtime varies with cache state and concurrent work, but the architecture is intrinsically expensive because a handful of new measurements cause the entire historical dataset to be rebuilt.

## Scheduler load

The long-running `atmoslink-scheduler.service` accumulated approximately 187,465 CPU seconds over about 9.3 days of uptime, equivalent to roughly 23% of one CPU core on average.

The current in-memory scheduler configuration differs from the tracked `config/scheduler.yaml`. Runtime-only tasks include `build_multistation_master` every 900 s and `scientific_hourly_6g` every 3600 s, while runtime `station_sync` is disabled even though the tracked YAML currently says enabled.

This means restarting the scheduler without first reconciling the YAML would change production behavior.

Latest task-duration ranking showed the principal scheduled costs:

- `enrich_master_dataset`: about 36 s every 300 s.
- `master_quality_check`: about 20 s every 300 s.
- stale scheduler `build_multistation_master`: roughly 29–45 s every 900 s.
- `notification_engine`: approximately 4 s every 60 s.
- `scientific_campaign_export`: approximately 41 s every hour.

## Dashboard

The Gunicorn dashboard runs two gthread workers. During the audit the service used about 1.0–1.15 GiB current memory and approximately 250 MiB swap. Individual worker PSS was roughly 436–543 MiB.

A 60-second sample while the UI was active showed the two workers together using about 25–26% of one CPU core.

The API receives repeated polling from the dashboard. In a 20-minute sample:

- `/api/station/latest`: 116 requests.
- `/api/station/history`: 78 requests, 13.36 MiB returned.
- `/api/scientific/hourly`: 38 requests, 3.66 MiB returned.
- `/api/v4/system-health`: 39 requests.

The multistation table currently has no indexes. SQLite query plans for station history and scientific hourly both perform a full table scan and a temporary B-tree for ordering.

Measured endpoint latency:

- SJ01 scientific hourly temperature: about 2.11 s.
- CU01 scientific hourly temperature: about 0.022 s.
- SJ01 history limit 120: about 0.43 s.
- CU01 history limit 120: about 0.85 s.

The SJ01 scientific-hourly route loads all qualifying SJ01 multistation rows with `SELECT *` into pandas and only then reduces them to hourly values.

## SQLite WAL

The physical WAL file was about 1.29 GiB. Direct read of the WAL-index header showed only approximately 30 frames in the current logical WAL cycle, so the large physical file does not by itself indicate a current 1.29 GiB uncheckpointed backlog. SQLite is reusing a previously enlarged WAL file.

The long-running weather logger has many open SQLite/WAL descriptors, but the count remained stable at 60 database-related descriptors over two consecutive 65-second observations. No current monotonic FD leak was demonstrated during this audit.

## Other observations

The scheduler log is approximately 246 MiB and `bme_diagnostic_raw.log` approximately 148 MiB; no AtmosLink logrotate rule was found. The BME diagnostic log remains active and grew by about 578 bytes during a 10-second sample.

Six abandoned Desktop Commander Python REPL sessions from earlier work were found idle for 3–8 days. They used approximately 52 MiB RSS in aggregate; these non-production sessions were terminated during the audit.

The older `epmp_monitor` capture pipeline remains active. It should not be retired solely because the earlier `epmp_logs` pollers were obsolete: `capture_agg_ap.sh` is still running and writes RF records into the current AtmosLink SQLite database.

## Priority

The highest-value optimization is to decouple the expensive full `build_multistation_master` rebuild from the two-minute SJ01 transfer cycle while preserving raw synchronization frequency and dashboard freshness.

A safe implementation should also reconcile the scheduler YAML before any scheduler restart, preserve the hourly 6 GHz scientific product, and explicitly keep the obsolete `station_sync` path disabled.

The dashboard query/index issue is the second priority. Any index change must be implemented in the builder itself because the builder recreates the multistation table; manually created indexes would otherwise disappear on the next rebuild.

No production service was restarted as part of this audit.
