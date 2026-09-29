# CU01 multistation rebuild optimization — 2026-09-29

## Objective

Reduce CPU, RAM and disk I/O on CU01 without reducing the two-minute raw SJ01 synchronization cadence or altering scientific source data.

The expensive operation was the complete rebuild of `master_observations_multistation` after each remote synchronization. The derived table contained about 170k rows, while each normal SJ01 transfer added only 1–2 rows.

## Configuration reconciliation

`config/scheduler.yaml` was reconciled with the long-running production state before restarting the scheduler:

- `station_sync` is explicitly disabled because `atmoslink-remote-sync.timer` is the canonical remote synchronization path.
- `scientific_hourly_6g` remains enabled every 3600 s.
- `build_multistation_master` is checked by the scheduler every 60 s.
- The builder itself enforces a global 300 s minimum between successful full rebuilds.

This one-minute check interval is intentionally shorter than the rebuild interval. Cheap skipped checks do not postpone the next eligible full rebuild by another five minutes.

## Builder guard

`weather_station.sync.build_multistation_master` now uses:

- an advisory `flock` to prevent concurrent full rebuilds;
- `runtime/multistation_build_state.json` to record the last successful full rebuild;
- a global minimum rebuild interval of 300 s;
- invocation-context detection from the Linux cgroup for provenance;
- the same effective 300 s minimum for scheduler and remote-sync invocations.

The central scheduler checks every minute, while the existing systemd `ExecStartPost` in remote-sync remains available after each transfer. Whichever eligible invocation obtains the lock first performs the rebuild; all intervening calls exit cheaply instead of rebuilding every two minutes.

`ATMOSLINK_MULTISTATION_FORCE=1` can bypass the interval guard for an explicit manual recovery run, while the concurrency lock remains active.

## Runtime transition

The scheduler was allowed to become idle and its user-owned main process was terminated cleanly. The existing systemd `Restart=always` policy restarted it and loaded the reconciled YAML. No systemd unit file required modification and no root-level service change was made.

After restart, the runtime registry matched the tracked scheduler configuration: `station_sync=false`, `build_multistation_master` enabled with a 60 s check interval, and `scientific_hourly_6g` enabled hourly.

## Observed result

A pre-optimization remote-sync cycle at 17:55 transferred two SJ01 rows and then performed a full rebuild. The service consumed 33.335 s CPU time and reached about 1.3 GiB peak memory.

After the final guard was active:

- 17:57 remote-sync transferred one row, skipped the fresh master, and consumed 1.271 s CPU.
- 17:59 remote-sync transferred two rows, skipped the fresh master, and consumed 1.376 s CPU with a 9.6 MiB service memory peak.
- 18:01 the scheduler started the eligible full rebuild. A simultaneous remote-sync transferred one row, detected the build lock, skipped its rebuild, and consumed 1.441 s CPU.
- The scheduler-owned full rebuild completed at 18:02:08 and wrote build state with `invocation_context=scheduler`.
- 18:03 remote-sync transferred two rows, skipped the fresh master at age 92.1 s, and consumed 1.264 s CPU.

The full rebuild remained approximately a 29 s operation, but it is no longer repeated every two-minute raw synchronization cycle.

## Data-path verification

Raw SJ01 synchronization remained active throughout the change, with zero ignored rows in the observed cycles.

At verification time, `station_observations` for SJ01 was current through 18:04 local time, while the derived multistation master was current through 18:00 local time. This expected four-minute lag is within the dashboard's canonical ONLINE window.

The dashboard returned HTTP 200 for both `/api/health` and `/api/station/latest?station_id=SJ01`; health status was `healthy`.

No raw scientific observation, historical CSV, or SQLite source row was deleted or rewritten by the cadence change. Only the derived master rebuild schedule and its execution guard changed.

## Provenance

Tracked file hashes before the change:

- `config/scheduler.yaml`: `5a6d9923d0b7e80bc74e62d6884f3a3af59e4ee87eef70cc07094567496fc865`
- `weather_station/sync/build_multistation_master.py`: `b08f471842be5cf5d63f688c6aa99f208bfcf9a4ad8707aeb6ada36e2a1fc6b2`

Hashes after the verified change:

- `config/scheduler.yaml`: `bce8d2bac7e2f44d7a6899e6f93b2b103938c5ce88a24c20c7af17ba19e69953`
- `weather_station/sync/build_multistation_master.py`: `8697ae5f46f9c76d893725671926698f4c5c749f17933aac9457a6dd2a09ca15`

The pre-change scheduler configuration is also preserved outside Git under the protected AtmosLink provenance backup directory.
