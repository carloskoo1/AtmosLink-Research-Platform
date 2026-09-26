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

## Version 3: event and trajectory screening

DISCOVERY-001 v3 introduces event-level temporal analysis. A candidate must no longer rely only on row-level association or block-level enrichment.

### Dynamic feature eligibility
CU01 pressure is quarantined from transition derivatives for this experiment because the existing quality report contains 388 `PRESS_JUMP` alerts during the prevalidation period, including extreme jumps that can dominate standardized temporal derivatives. The pressure level may remain contextual, but its short-term derivative is not eligible for candidate generation in v3.

### Atmospheric transition event
A transition event is defined from 15-minute standardized changes across multiple atmospheric variables. At least two variables must exceed the activity threshold, extreme standardized values are clipped, local maxima are selected, and a 30-minute refractory period prevents repeated rows from representing one event multiple times.

### RF transition event
RF response is represented as a robust quality index derived from DL/UL RSSI, SNR and MCS. Version 3 studies sharp 15-minute drops in that index rather than only absolute low-quality states.

### Sensitivity and directionality
The sequence engine evaluates multiple atmospheric-event quantiles, RF-drop quantiles and future horizons. A block-level risk ratio greater than one is not sufficient for promotion. The RF event must occur strictly after the atmospheric event, and future-event risk must exceed past-event risk in both discovery and characterization.

### RFATM-0004
An apparent multivariate atmospheric-transition -> RF-drop relationship produced RR > 1 in both cohorts in 35 of 45 sensitivity cells. At the central exploratory setting, block-level RR was 1.263 in discovery and 2.006 in characterization. However, within a strict 60-minute temporal window, discovery contained 30 future versus 38 past RF-drop events, while characterization contained 13 future versus 14 past events. Therefore temporal direction failed and `RFATM-0004` was classified `SCREENED_OUT`.

This result demonstrates that threshold robustness alone is insufficient. Sequence candidates must satisfy independent temporal directionality before they can become hypotheses. D_validation and the external replication cohorts remain untouched.

## Version 3 trajectory discovery

The trajectory engine detects independent multivariate atmospheric transition events and tests whether specific transition archetypes precede entries into a robust RF-degradation state.

Rapid derivatives of CU01 pressure are currently excluded from trajectory discovery because the quality report contains 388 PRESS_JUMP warnings within the prevalidation interval. The pressure level may remain contextual, but its short-term derivative cannot generate a candidate until signal eligibility is restored.

A new intermediate status is introduced: EVIDENCE_ACCUMULATING. This state is used when a pattern preserves direction and relevant effect magnitude across discovery and characterization but the confidence intervals remain too wide for hypothesis promotion.

RFATM-0006 is currently EVIDENCE_ACCUMULATING. It represents an atmospheric transition archetype dominated by rapid warming and drying at SJ01. Approximate 15-minute physical changes at its center are +1.83 C temperature, -8.01 percentage points relative humidity, -0.08 hPa pressure and +0.38 m/s wind at SJ01, with little simultaneous change at CU01. At a 60-minute horizon, block-level RF degradation risk ratios are approximately 1.38 in discovery and 1.60 in characterization. However, both 95% confidence intervals include 1, so the candidate is not frozen and D_validation remains embargoed.
