# Reviewer B analog telemetry stress — prospective protocol

**Status:** specification written before the new audit is executed. This is a post-v21/v23 RF sensitivity analysis, not a replacement for their registered results.
**Background:** SHA-256 `eed7df2621f6952b9ea2eaa7524f735a706b69494d3d272fd2dd828b52a97387`, the 2,860-row D_development snapshot. Do not read D_validation or other configuration cohorts.
**Atmospheric hypotheses:** the frozen v21 four-driver library, event thresholds, 360-min refractory interval, four contiguous fold boundaries, and 30/60/120-min horizons. M3 selector: one-sided directional binomial p < 0.05/12, >=8 discordant events, positive direction in >=3 folds. The limitations of the test and shift null remain open under Reviewer A.

## RF perturbations and outcomes

- Resample to 5-min grid with the v21 method. Three separately evaluated outcomes: BOTH = mean robust-reference z of four analog fields; DL = mean of DL RSSI and DL SNR; UL = mean of UL RSSI and UL SNR. For each outcome, freeze its RF-drop threshold at the 7.5th percentile of the background three-bin score difference; six-bin event refractory.
- In every activated three-bin (15-min) interval, subtract exactly **2.0 dB** from both RSSI and SNR in the specified direction: BOTH, DL-only, or UL-only. This preserves the RSSI-minus-SNR implied noise floor within each affected direction. All MCS entries remain unchanged. Values are real-valued dB telemetry stresses; no attenuation mechanism, throughput outcome, or physical causal calibration is claimed.
- Registered lags: 15, 30, 60 min. Activation probability 0.70. One planted truth among four drivers. Exactly 100 seeded trials per driver × lag × perturbation morphology. Pair the activation draws across the three outcome detectors using `seed=530000+trial`. Assess all 3×3 morphology/outcome cells.
- Primary endpoints by morphology/outcome/lag: exact-truth selection, exclusive truth selection and distractor co-selection, pooled over 400 trials across four truths. Report per-driver rates and the number of detected RF events. No best-view selection or post-hoc detector promotion.
- Conditional surrogate-null diagnostic: jointly circular-shift all four driver event sets by one common offset drawn from `[72, n-72)` using RNG seed 2026092609, 1000 trials per outcome, comparing against unchanged analog background events. Reuse offsets across outcomes. This is a surrogate rate only; it cannot close Reviewer A.
- Output version `v25_reviewer_b_analog_stress`; CSV trials, CSV metrics, JSON summary with source/protocol hashes, code commit, thresholds, scales and counts. Verify source hash and clean Git state before executing. Keep old v21/v23 results intact.

**Interpretive rule:** changes in recovery demonstrate dependence on perturbation morphology and RF outcome. An analog stress is more admissible numerically than fractional MCS injection, but does not establish a path-loss, precipitation, or radio-failure model. Reviewer B remains open until operational and external physical validation is separately addressed.
