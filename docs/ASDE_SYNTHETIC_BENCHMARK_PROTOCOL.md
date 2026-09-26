# ASDE Synthetic Ground-Truth Benchmark — Frozen Protocol v1

## Purpose
Quantify whether the AtmosLink Scientific Discovery Engine (ASDE) can recover known injected temporal atmospheric-to-RF patterns while controlling false positives on the real AtmosLink development background.

This benchmark does not use D_validation and is not a substitute for real-world confirmatory validation.

## Frozen background
- Dataset: DISCOVERY-001 prevalidation development snapshot.
- Rows: 2860 complete-core observations before 5-minute resampling.
- Confirmatory real-data holdout D_validation remains embargoed.

## Synthetic driver
The driver is derived only from SJ01 atmospheric data:
- 15-minute temperature change;
- 15-minute relative-humidity change;
- robust standardized score = warming minus humidity decrease;
- candidate driver events are local peaks above the 85th percentile;
- minimum refractory spacing = 180 minutes.

The 180-minute spacing is frozen to prevent pre/post contamination for candidate lags up to 60 minutes and analysis horizons up to 120 minutes.

## Injection grid
- RF effect magnitude: 0.5, 1.0, 1.5, 2.0 robust SD.
- Lag: 15, 30, 60 minutes.
- Duration: 15 minutes.
- Activation probability per eligible driver event: 0.70.
- RF variables shifted jointly: DL/UL RSSI, DL/UL SNR, DL/UL MCS.
- 100 independent confirmatory simulation seeds per effect-lag cell.

## Detection horizons and multiplicity
Candidate horizons: 30, 60, 120 minutes.
Family-wise alpha = 0.05.
Bonferroni alpha per horizon = 0.05/3.

A trial is recovered if at least one horizon satisfies all:
1. one-sided exact pre/post direction p < 0.05/3;
2. at least 8 discordant driver events;
3. post-event RF entries exceed pre-event RF entries in at least 3 of 4 contiguous development folds.

## Empirical null
- 1000 independent circular-shift trials.
- Atmospheric driver timing is shifted while preserving its internal spacing.
- RF background is unchanged.
- The same family-wise detection rule is applied.
- Primary false-positive endpoint: proportion of null trials detected.

## Frozen reporting
Report Wilson 95% confidence intervals for recovery proportions and empirical family-wise false-positive rate.
No benchmark thresholds, event spacing, horizons, effect sizes, lags, or decision gates may be changed after viewing the confirmatory seeds.

## Frozen RF-event detector
The RF event detector is also frozen before simulation:
- robust RF quality is computed from DL/UL RSSI, SNR and MCS;
- the RF reference medians/scales are estimated once from the unmodified D_development background;
- an RF drop is defined from the 15-minute RF-quality change;
- the drop threshold is the 7.5th percentile of the unmodified development background;
- frozen numeric threshold: -0.5620817932460992;
- this threshold must not be recalculated after synthetic effects are injected.

## Audit-grade randomization
The post-freeze confirmatory run will use:
- injected-trial seeds 90000 through 90099 for every effect-lag cell;
- 100 trials per effect-lag cell;
- null circular-shift RNG seed 2026092602;
- 1000 null trials.

These seeds are reserved for the audit-grade run and must not be used during benchmark development.
