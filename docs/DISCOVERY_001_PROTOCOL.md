# DISCOVERY-001

## Purpose
AI-assisted discovery of reproducible atmospheric-radioelectric patterns in the AtmosLink 6 GHz rural high-altitude link.

## Primary cohort
- Frequency: 7000 MHz
- Channel bandwidth: 20 MHz
- Source: `Data/exports/scientific_campaign_6g_integrated.csv`
- Source SHA-256: `2c19cc4ee1a66d23765bb79cc9eb840c1c531b3833ea72e8ffba848a0c96ff6c`
- Complete core observations: 3576

## Core variables
RF: DL/UL RSSI, DL/UL SNR, DL/UL MCS.
Atmospheric: CU01 temperature, humidity, pressure; SJ01 temperature, humidity, pressure, wind speed.

## Scientific rule
The AI may propose candidate patterns and hypotheses. It may not label a pattern as scientifically confirmed. Confirmation requires frozen hypotheses, independent validation data, reproducibility, statistical evaluation, and human scientific review.

## Frozen temporal split
The primary cohort is split chronologically, never randomly.

- `D_discovery`: 2145 rows; 2026-09-01 18:30:52 UTC to 2026-09-09 18:41:57 UTC.
- `D_characterization`: 715 rows; 2026-09-09 18:46:58 UTC to 2026-09-13 03:29:49 UTC.
- `D_validation`: 716 rows; 2026-09-13 03:34:50 UTC to 2026-09-16 03:51:31 UTC.

`D_validation` is embargoed from discovery and characterization. Its contents may only be used after a candidate hypothesis has been frozen.

## External replication cohorts
The following configurations are reserved for later cross-configuration replication:
- 6475/20 MHz: 855 complete-core rows.
- 6655/20 MHz: 583 complete-core rows.
- 7000/40 MHz: 623 complete-core rows.
- 6655/40 MHz: 582 complete-core rows.

## State model
`CANDIDATE -> SCREENED_OUT` or `CANDIDATE -> HUMAN_REVIEWED -> HYPOTHESIS -> FROZEN -> VALIDATING -> CONFIRMED | REJECTED | INCONCLUSIVE`

## Version 2 safeguards

DISCOVERY-001 v2 separates atmospheric-state discovery from RF-degradation definition. Atmospheric states may be learned from meteorological variables and their temporal descriptors, but RF variables are excluded from the atmospheric representation.

RF degradation is defined independently using a robust quality index constructed from DL/UL RSSI, SNR and MCS. The degradation threshold is learned from D_discovery only and is then frozen for characterization.

### Ablation requirement
A candidate originating from clustering must be tested across multiple state counts and initialization seeds. A pattern that only appears under one arbitrary clustering configuration cannot be promoted.

### Temporal-independence requirement
Repeated 5-minute rows are not treated as independent evidence. Candidate patterns must survive aggregation into coarser non-overlapping temporal blocks or an equivalent event/episode-level analysis before promotion to hypothesis.

### Current screened candidates
- RFATM-0001: pressure-SNR/RSSI association; screened out for lack of characterization stability.
- RFATM-0002: humidity-MCS association; screened out after temporal-cycle control.
- RFATM-0003: recurrent cold-humid-calm regime; screened out after 30-minute block-level replication reversed in characterization.

No candidate has been frozen. D_validation remains embargoed.
