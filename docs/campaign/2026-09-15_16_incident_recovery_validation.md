# AtmosLink 3×2 — Incident recovery and scientific validation

**Period:** 2026-09-15 to 2026-09-16 (America/Lima)
**Campaign:** ANDEAN 6 GHz 3×2 2026
**Design:** 3 operating frequencies × 2 channel bandwidths
**Link:** CU01 (Cuñacales) ↔ SJ01 (San José), Cajamarca, Peru; ~12 km LoS
**Current validated scenario:** F6655_B20 = 6655 MHz / 20 MHz

## Scientific purpose

The campaign evaluates how frequency and channel bandwidth affect a real high-altitude rural 6 GHz radio link. Each controlled scenario integrates RF telemetry, active network measurements and simultaneous meteorological observations at CU01 and SJ01. Variables include RSSI, SNR, MCS, link indicators, throughput, RTT/retransmission evidence where available, and atmospheric variables.

## Incident — 2026-09-15

The first scheduled transition to F6655_B20 did not complete normally. The AP accepted the trial configuration, but end-to-end connectivity was subsequently lost and the normal cancellation/recovery path did not restore service. SM and remote-site connectivity were unavailable during the incident interval.

Recovery was conservative: the protected 5.8 GHz path was not modified. A controlled intervention on the 6 GHz path restored the AP/SM/RPi chain. The link was recovered under the previous configuration and later transitioned under supervision to 6655 MHz / 20 MHz. The failed interval is retained as incident evidence and must not be relabeled as valid F6655_B20 experimental data.

## Recovery and stabilization

Independent RF telemetry captured the previous configuration, a temporary collection-error interval and stable dual-ended operation at 6655/20. Stable F6655_B20 operation was observed from at least 2026-09-15 23:01:35 -05:00. Executor reconciliation occurred at 23:38:35 -05:00; that is an administrative timestamp, not the physical start of scientifically valid RF operation.

## Hardening after the incident

The campaign executor was strengthened with a persistent SAFE_ABORT barrier, fail-closed recovery diagnostics, strict validation of target PoE-delivering state, bounded RF retries per sequence, correct retry-counter reset between sequences, and improved Cambium API session/logout lifecycle. The campaign timer was subsequently reactivated and verified to behave idempotently when the active scenario was already applied.

Executor state was reconciled to sequence 1 / F6655_B20. At the Sep 16 validation neither an active SAFE_ABORT marker nor an active executor_failure.json was present. Archived failure evidence was preserved rather than overwritten.

The next nominal transition remains **2026-09-18 00:00 -05:00**, from **F6655_B20 (6655/20)** to **F7000_B40 (7000/40)**. The Sep 15 incident does not shift the nominal schedule; affected observations are handled by validity classification/exclusion rather than schedule rewriting.

## Scientific integration validation — 2026-09-16

A read-only validation was performed on Controlador and rpi-sanjose64 at approximately 10:29–10:33 -05:00.

| Dataset | Rows | Latest timestamp |
|---|---:|---|
| weather_local | 106,357 | 2026-09-16 10:29:36 -05:00 |
| radio_link_local | 48,956 | 2026-09-16 10:29:30 -05:00 |
| active_throughput_6g | 2,602 | 2026-09-16 10:05:44 -05:00 |
| scientific_campaign_6g_integrated | 4,259 | 2026-09-16 09:43:50 -05:00 |

The integrated dataset advanced beyond the pending watermark 2026-09-15 23:36:42 -05:00. For new F6655_B20 records after that watermark, **121** integrated RF observations were found: SJ01 weather matched **121/121**, CU01 **119/121**, and simultaneous CU01+SJ01 **119/121**. The five most recent inspected records were `LINK_OPERATIONAL_DUAL` with both weather stations matched. The two records without CU01 matching are retained unchanged and are not imputed.

## Multisite meteorological continuity

At validation time, `master_observations_multistation` contained **104,439 CU01 rows**, latest weather 10:29:36 -05:00, and **35,145 SJ01 rows**, latest weather 10:28:45 -05:00. This confirms current ingestion from both field stations.

On rpi-sanjose64, `weather-logger-sj01.service` was active and valid `RX_VALIDO` / `GUARDADO` observations continued. Known intermittent non-UTF-8/0xFF serial fragments remained observable, but valid acquisition continued after the warnings; they did not constitute a logger outage in this validation.

## Methodological conclusion

The post-recovery scientific chain was validated:

**F6655_B20 RF → CU01 weather → SJ01 weather → multisite consolidation → active throughput → integrated scientific dataset.**

The operational decision is **collection mode / no intervention**: keep 6655 MHz / 20 MHz unchanged until the scheduled transition, avoid unnecessary RF/PoE/VLAN/service changes, and continue automated read-only supervision and daily traceability.

## Provenance and interpretation

This record does not imply that every Sep 15 observation is experimentally valid. Physical RF transition time, administrative executor reconciliation, acquisition continuity and scientific-validity classification are intentionally distinguished. Incident evidence is preserved so later analysis can classify or exclude affected intervals reproducibly.
