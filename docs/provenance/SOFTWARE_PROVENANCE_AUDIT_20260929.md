# AtmosLink Software Provenance Audit v1 — 2026-09-29

Audit started from CU01/Controlador branch `feature/scientific-discovery-001`, commit `7469a1cfc8e9def91d557c0e4c33568ddb879902`, at `2026-09-29T12:55:51-05:00`.

## Purpose

Ensure that operational acquisition, synchronization, telemetry, validation, dashboard and watchdog software can be traced to a versioned source or an immutable hash manifest.

## CU01 findings

All principal AtmosLink Python entrypoints invoked by systemd are tracked in the repository at the audit baseline. The live CU01 systemd deployment was only partially represented in Git before this audit: dashboard and event-monitor units were tracked, while the remaining live AtmosLink units, timers and drop-ins were not. This audit captures the exact live unit files and effective drop-ins under `deploy/systemd/cu01/`.

The CU01 weather watchdog previously existed only at `/usr/local/sbin/atmoslink-weather-watchdog.py`; this audit captures the exact script under `deploy/watchdog/`.

The dashboard base unit is identical to its pre-existing tracked copy. Its effective Gunicorn command is supplied by the deployed override drop-in, whose SHA-256 matches the pre-existing tracked override.

The effective remote-sync runtime lock path is supplied by a deployed drop-in; that drop-in is now captured.

## SJ01 finding requiring separate field-state snapshot

SJ01 is running branch `feature/sj01-multisensor-config` at baseline commit `4cd672ef599a77f65e0f6fd9a616d523bd9665c3`. Its production `weather_station/logger/logger_weather.py` contained an uncommitted FF64 diagnostic instrumentation change at audit start. The field node must preserve that exact state in a dedicated provenance commit without automatically reconciling it with the newer CU01 branch.

## Legacy ePMP cron

CU01 still has cron references to scripts under `/home/carlos/epmp_logs` and `/home/carlos/epmp_monitor/bin`. Their hashes are recorded in `provenance/legacy_cron_CU01_20260929.csv`. Their source is not copied blindly because at least one file contains a possible literal credential/token and requires sanitization before normal Git versioning.

## Firmware

Recovered SJ01 firmware build provenance is recorded under `provenance/firmware/SJ01_20260804/`. Normal Git stores manifests and provenance metadata; large firmware build artifacts should be archived externally/released immutably and verified by SHA-256.

## Rule from this audit

No production component should exist only in `/etc/systemd`, `/usr/local/sbin`, a Raspberry Pi working tree, an Arduino cache, or a laptop directory. Runtime source, deployment descriptors and provenance metadata must be versioned; secrets and databases must remain outside Git.
