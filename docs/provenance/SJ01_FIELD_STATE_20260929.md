# SJ01 field software state — 2026-09-29

Captured at `2026-09-29T12:55:55-05:00` on Linux host `rpi-cunacales`, Tailscale IPv4 `100.104.97.100`.

Baseline Git branch: `feature/sj01-multisensor-config`.
Baseline Git commit before provenance commit: `4cd672ef599a77f65e0f6fd9a616d523bd9665c3`.

The production logger had one tracked-but-modified file before this audit:

`weather_station/logger/logger_weather.py`

Its field SHA-256 at capture time is:

`f5d59d2d9eef6d95e685f0933b90ad220dd8d4221ad0f14f04b90db784ea9da6`

The modification adds bounded raw-hex diagnostics for strict UTF-8 failures observed during the FF64 investigation. This state is preserved as field provenance; it is not automatically reconciled with the newer CU01 branch.

Exact live SJ01 systemd units are captured under `deploy/systemd/sj01/`. The previously external watchdog script is captured under `deploy/watchdog/`.

No credentials, SQLite databases, serial captures, or environment-secret files are added by this snapshot.
