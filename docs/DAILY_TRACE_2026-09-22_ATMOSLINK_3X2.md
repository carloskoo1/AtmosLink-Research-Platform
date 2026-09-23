# AtmosLink 3×2 — Daily traceability — 2026-09-22

Read-only inspection from Controlador at 2026-09-23 00:36–00:38 -05:00. No RF, PoE, VLAN, service, timer, or database configuration was changed.

## Scenario and RF

- Executor: sequence 3, `F6475_B20`, applied `2026-09-21T00:00:00.790372-05:00`.
- Scenario: 6475 MHz / 20 MHz. `andean-campaign.timer` active; executor repeatedly reports `Sin transición: F6475_B20 ya fue aplicado`.
- `SAFE_ABORT`: absent. `executor_failure.json`: absent.
- Latest RF: 2026-09-23 00:37:17 -05:00; MCS DL/UL 105/101, SNR 22/18 dB, station RSSI -77/-84 dBm, DL rate 68 Mbps, note `ok`, no error.

## Weather

- CU01 continues at one-minute cadence. Latest: 2026-09-23 00:37:46 -05:00; 17.55 °C, 68.80 % RH, 741.94 hPa, rain 1 min/1 h = 0/0 mm; BME/rain flags OK.
- Direct read-only access to `rpi-sanjose64` could not be established. Tailscale reports it active, but SSH policy/authentication prevented a direct session.
- Central SJ01 synchronization is failing: at 00:32 and 00:34 the synchronizer timed out checking `weather-logger-sj01.service`; central `source_local_id` remained 40388. This is a synchronization incident, not proof that the SJ01 logger itself is stopped.

## Active throughput

- `active_throughput_6g`: 3,222 rows; advances through 2026-09-23 00:30:19 -05:00.
- Latest F6475_B20 pair: DL 30.890 Mbps / 50 retransmissions; UL 9.434 Mbps / 17 retransmissions; 0 % ping loss; RTT avg 3.356 ms.
- Associated RF: RSSI -78/-85 dBm, SNR 21/17 dB, MCS 104/102. CU01 weather matched at 00:29:46; SJ01 weather unavailable in these rows.

## Integrated datasets

- `master_observations_multistation`: 148,443 rows; latest timestamp 2026-09-20T16:34:07-05:00. It has not advanced into F6475_B20.
- `scientific_campaign_6g_integrated`: 5,253 rows; latest RF timestamp 2026-09-20T16:31:04-05:00, still F7000_B40. Current F6475_B20 has not yet reached this integrated table.
- Scientific validation completed OK for CU01/SJ01 at 2026-09-23 00:28:36 -05:00, but its analyzed horizon ends at 2026-09-20T21:00:00Z; this does not prove current SJ01 synchronization.

## F6655_B20 watermark validation

`scientific_campaign_6g_integrated` has advanced beyond `2026-09-15T23:36:42-05:00`: 1,115 later rows exist, through 2026-09-20T16:31:04-05:00.

For F6655_B20 after that watermark: 578 rows; SJ01 matched 578/578, CU01 575/578, both 575/578. Therefore the validation is closed as **not 100 % dual-matched**. Three CU01 exceptions are preserved without imputation:

- 2026-09-16T01:27:01-05:00 — CU01 unmatched; SJ01 matched, delta 1 s.
- 2026-09-16T07:28:19-05:00 — CU01 unmatched; SJ01 matched, delta 19 s.
- 2026-09-16T22:41:16-05:00 — CU01 unmatched; SJ01 matched, delta 16 s.

## Services, backup, and incidents

Active/normal at inspection: campaign timer, dashboard, scheduler, event monitor, remote-sync timer, remote-backup timer, independent 6 GHz throughput timer, and scientific-validation timer. The campaign executor is a oneshot and is normally inactive between triggers.

Backup for 2026-09-22 completed successfully: `backup_CU01_20260922_024436.zip`, 139,111,134 bytes, uploaded and verified in both configured Google Drive destinations; completed 02:53:54 -05:00.

`andean-throughput.service` is failing hourly with rc=2 because its wrapper passes CLI arguments no longer accepted by `active_throughput_6g.py`. The independent `atmoslink-throughput-6g.timer` continues producing rows, so this is a formal-measurement path incident, not total throughput acquisition loss.

At the consolidation boundary, `atmoslink-remote-sync.service` is failed due to SJ01 SSH timeouts. Legacy `tailscale-serve-ap.service` also remains failed and is not evidence of RF failure.

## Methodological decision

Preserve F6475_B20 and raw acquisition unchanged. Do not impute the three historical F6655_B20 CU01 weather gaps. Do not claim current dual-station integration until SJ01 synchronization and the master/integrated datasets advance again. No recovery or human configuration change was performed during this inspection.

### Classification

- Normal operation: F6475_B20 RF telemetry, CU01 weather, independent active throughput, campaign scheduler, validation engine, and dual remote backup.
- Incidents: SJ01 central synchronization timeout; formal hourly throughput wrapper CLI incompatibility; master/integrated datasets stale since 2026-09-20.
- Human/recovery actions during this consolidation: none.
