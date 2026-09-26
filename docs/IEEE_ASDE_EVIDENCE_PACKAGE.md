# IEEE ASDE Evidence Package

> Historical evidence snapshot. Its original FWER/CI and full-gate wording predates the Reviewer A audit. For current claims use `IEEE_ASDE_FULL_DRAFT_V1.md`, `IEEE_ASDE_CLAIM_LEDGER.md`, and `IEEE_ASDE_REVIEWER_A_STATISTICAL_AUDIT.md`; do not reuse the abstract or statistical interpretation below without those corrections.

## Working title
**ASDE: An Auditable AI-Assisted Scientific Discovery Engine for Atmospheric–Radioelectric Pattern Screening in a Rural High-Altitude 6 GHz Link**

## Central research question
Can an AI-assisted discovery workflow identify candidate atmospheric–radioelectric structures while controlling false discoveries, temporal leakage, pseudoreplication, and adaptive overfitting in real operational wireless-link data?

## Core contribution
The contribution is not a claimed meteorological cause of RF degradation. The contribution is an auditable discovery methodology that separates:
1. exploratory candidate generation;
2. QC eligibility;
3. temporal-independence screening;
4. strict pre/post directionality;
5. multiplicity control;
6. context markers from precursors;
7. frozen hypotheses from development findings;
8. real-data holdout validation.

## Empirical setting
- Real rural high-altitude 6 GHz link.
- Multisite local weather + RF telemetry.
- Development snapshot: 2860 complete-core observations.
- Real confirmatory holdout: 716 observations, analytically isolated from candidate selection, tuning, screening, and benchmark development.
- Development is evaluated using four contiguous temporal folds.

## Real-data discovery outcome
Six atmospheric–RF candidates were generated and subsequently screened out before validation. Failures included lack of temporal replication, diurnal/trend confounding, pseudoreplication, strict directionality failure, and multiplicity/control-support failure.

One exploratory context association (CTX-0001) was retained for sensitivity analysis: lower 60-minute SJ01 humidity variability around RF-quality drop episodes relative to same-clock controls. Subsequent outcome-definition sensitivity showed that the association is present under the all-metric, analog-only, and UL-oriented RF event definitions but absent under the DL-only definition. CTX-0001 is therefore classified as an outcome-definition-sensitive context association, not as a robust marker or precursor.

## Audit-grade synthetic benchmark
Frozen protocol commit: **1e49129**.

The final benchmark uses:
- real AtmosLink development background;
- atmospheric driver events separated by 180 minutes;
- fixed RF-drop threshold learned only from unmodified development data;
- 0.5, 1.0, 1.5, and 2.0 robust-SD injected RF effects;
- 15, 30, and 60 minute lags;
- 100 independent seeds per effect-lag cell;
- 1000 circular-shift null trials;
- three analysis horizons with Bonferroni family-wise correction;
- temporal-direction consistency required in at least 3 of 4 folds.

### Primary benchmark results

| Injected effect | Lag 15 min | Lag 30 min | Lag 60 min |
|---|---:|---:|---:|
| 0.5 robust SD | 1.00 | 0.84 | 0.62 |
| 1.0 robust SD | 1.00 | 1.00 | 0.94 |
| 1.5 robust SD | 1.00 | 1.00 | 0.97 |
| 2.0 robust SD | 1.00 | 1.00 | 0.97 |

Empirical family-wise false-positive rate: **0.025**, Wilson 95% CI **[0.0170, 0.0366]**.

For a 1.0 robust-SD planted effect, family-wise recovery was 100% at 15 and 30 minutes and 94% at 60 minutes.

## Interpretation
The synthetic benchmark demonstrates that the frozen ASDE screening rule is conservative under null circular shifts while retaining high recovery for moderate planted effects. The benchmark also quantifies the sensitivity loss for weaker and longer-lag effects.

These results validate the discovery machinery, not a specific natural atmospheric causal effect.

## Candidate IEEE figures
1. ASDE architecture and state machine.
2. Candidate attrition diagram: generated -> screened out -> context marker -> frozen hypothesis.
3. Audit-grade family-wise recovery vs injected effect size, stratified by lag.
4. Detection surface: injected lag vs analysis horizon at 0.5 SD.
5. Detection surface: injected lag vs analysis horizon at 1.0 SD.
6. Timeline showing D_development and untouched D_validation.

Current generated vector figures:
- figure_familywise_recovery.svg
- figure_detection_surface_0p5sd.svg
- figure_detection_surface_1p0sd.svg

## Manuscript structure
I. Introduction  
II. Related Work  
III. AtmosLink Experimental Platform  
IV. ASDE Architecture  
V. Adaptive Discovery and Holdout Protection  
VI. Ground-Truth Synthetic Benchmark on Real Background Data  
VII. Real-Data Case Study and Candidate Attrition  
VIII. Discussion  
IX. Limitations  
X. Conclusion

## Claim discipline
The paper may claim quantitative performance of ASDE on the frozen synthetic benchmark and may describe CTX-0001 only as an exploratory, outcome-definition-sensitive real-data association. It must not claim that weather causes RF degradation in the natural data unless a future frozen hypothesis succeeds on D_validation and subsequent external replication.

## Audit-grade safeguard ablation
Using the same audit-grade trials, the naive uncorrected rule produced an empirical family-wise false-positive rate of **0.079**, whereas the full ASDE gate produced **0.025**. For a 1.0 robust-SD injected effect, the full gate retained recovery of 1.00, 1.00, and 0.94 at lags of 15, 30, and 60 minutes, respectively. This supports the claim that the safeguards reduce false alarms without materially sacrificing moderate-effect sensitivity in the tested regime.

Generated ablation figure:
- figure_ablation_false_positive.svg

## Editorial positioning
IEEE Access currently defines a Methods article as work reporting a new experimental, measurement, or mathematical technique. This is the recommended manuscript type for ASDE. The manuscript should emphasize the auditable method and quantitative benchmark, with the AtmosLink natural-data analysis presented as a case study and stress test rather than as a causal weather result.

## Out-of-family robustness stress test
A post-audit exploratory stress test challenged the primary detector with alternative RF perturbation morphologies using 100 trials per cell. At 1.0 robust SD per affected metric, an abrupt joint 15-minute degradation was recovered at 1.00, 1.00 and 0.98 for 15/30/60-minute lags; a 60-minute sustained joint degradation also yielded 1.00, 1.00 and 0.98; a 30-minute joint ramp yielded 1.00, 1.00 and 0.77. By contrast, RSSI-only, SNR-only and MCS-only 15-minute perturbations each yielded 0.74, 0.50 and 0.08. These values are supportive robustness evidence, not part of the preregistered primary audit benchmark. They show that the current composite RF detector is substantially less sensitive to single-subsystem perturbations and to longer-lag gradual effects.

## Audit-grade hidden-driver benchmark (v21)
The known-driver v12 benchmark validates the statistical screening gate but does not by itself establish discovery performance. v21 therefore freezes a finite four-driver atmospheric hypothesis library and hides the planted true driver from the search procedure.

Frozen execution commit: **63839e8**. Development snapshot SHA-256: `eed7df2621f6952b9ea2eaa7524f735a706b69494d3d272fd2dd828b52a97387`. Protocol SHA-256 recorded by the audit: `8b81d904dce6fa1636f3bbf39edcc80081ce1a48a09001a1cb3fd9da2de1487d`.

Library-wide circular-shift null FWER = **0.020**, Wilson 95% CI **[0.0130, 0.0307]**. For 1.0 robust-SD joint RF effects, exact-driver selection was **0.8525**, **0.7900**, and **0.2125** at 15/30/60-min lags, while unique top-1 ranking was **0.9450**, **0.8950**, and **0.5950**. No distractor co-selection occurred in the 400 trials of each aggregate effect-lag cell.

The difference between ranking and gate-passing selection is intentional evidence of conservatism: at longer lags the true driver may rank first but still fail the prespecified evidence threshold. v21 supports claims only for recovery within this finite, prespecified, temporally screened library; it does not establish arbitrary hypothesis discovery.

## Post-audit background-hardness diagnostic (v22)
Recovery is heterogeneous across drivers because the real RF background is not neutral around all atmospheric event families. Baseline pre/post RF-event asymmetry is favorable for some drivers and adverse for others. Therefore aggregate recovery is accompanied by per-driver results, and v22 is diagnostic only; it is not used to retune v21.
