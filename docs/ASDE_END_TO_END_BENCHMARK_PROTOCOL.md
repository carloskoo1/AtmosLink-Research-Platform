# ASDE End-to-End Hidden-Driver Benchmark — Frozen Protocol v1

## Purpose
Evaluate whether ASDE can recover the correct atmospheric driver from a finite set of competing hypotheses when the true driver is hidden from the search procedure. This benchmark targets the discovery+screening pipeline, whereas the earlier v12 audit benchmark primarily validates the screening gate for a known driver.

The real confirmatory D_validation remains embargoed and is not used here.

## Candidate-library design
The library is selected using atmospheric data only, before evaluating RF recovery under this protocol.

Design constraints:
- 15-minute atmospheric changes.
- Event threshold: 85th percentile of each robust standardized driver score.
- Event refractory interval: 360 minutes.
- Minimum 20 events per candidate driver.
- Temporal proximity audit: pairwise event overlap within +/-60 minutes must be <=0.35.
- Candidate set chosen as the exact maximum independent set under the overlap graph; if multiple sets have the same size, prefer the set with larger minimum event support, then larger median support.

This rule was selected after an atmospheric-only identifiability tradeoff analysis (v20) and before the audit-grade hidden-driver RF benchmark.

## Frozen candidate library
1. cu01_local_temp_avg_c__rise — 23 events; score threshold 1.5308007671599377.
2. sj01_local_temp_avg_c__fall — 28 events; score threshold 1.2876641771825945.
3. sj01_local_hum_avg_pct__fall — 28 events; score threshold 1.6365945597866016.
4. sj01_local_press_hpa__rise — 28 events; score threshold 0.8993210126363124.

The library size is therefore 4 candidate drivers.

## Synthetic RF ground truth
For each trial, exactly one library driver is designated as the hidden truth.

Injection:
- joint abrupt degradation across DL/UL RSSI, SNR and MCS;
- per-metric magnitude: 0.5, 1.0 or 1.5 robust SD;
- lag: 15, 30 or 60 minutes;
- duration: 15 minutes;
- activation probability: 0.70 per eligible true-driver event;
- RF reference medians/scales and RF-drop threshold are learned once from the unmodified development background;
- frozen RF-drop threshold: -0.5620817932460992.

## Blind discovery search
The search algorithm receives all four candidate event sets and the resulting RF event series but is not given the planted truth.

For every driver, three response horizons are tested: 30, 60 and 120 minutes.

Family-wise hypothesis universe:
4 drivers x 3 horizons = 12 tests.

Bonferroni alpha per driver-horizon test:
0.05 / 12 = 0.004166666666666667.

A driver is selected if at least one horizon satisfies all:
1. one-sided exact pre/post direction p < 0.05/12;
2. at least 8 discordant events;
3. post-event RF entries exceed pre-event entries in at least 3 of 4 contiguous development folds.

## Primary endpoints
1. **Exact-driver recovery:** proportion of trials in which the planted driver passes the selection gate.
2. **Exclusive exact-driver recovery:** proportion in which the planted driver passes and no distractor passes.
3. **Unique top-1 ranking accuracy:** proportion in which the planted driver has the uniquely smallest minimum unadjusted directional p-value across candidate drivers. Ties for the smallest p-value are classified as ranking-ambiguous, not as correct top-1 recovery. This is a ranking metric and does not imply selection.
4. **Distractor co-selection:** proportion in which at least one non-truth driver also passes.
5. **Mean selected-driver count.**
6. **Library-wide null FWER:** probability that any driver is selected under a circular-shift null.

All proportion estimates report Wilson 95% confidence intervals.

## Audit randomization
- 100 independent injection trials per truth-driver x effect-size x lag cell.
- Injection seeds reserved: 310000–310099.
- 1000 library-wide circular-shift null trials.
- Null RNG seed reserved: 2026092605.
- Circular shift is applied jointly to all four atmospheric driver event sets so their cross-driver dependence structure is preserved relative to each other while broken relative to RF events.

## Claim limits
This benchmark can support quantitative claims about recovery of a hidden driver within this **finite, prespecified and temporally separable candidate library**. It cannot establish open-ended discovery over arbitrary hypotheses, causal correctness of natural atmospheric effects, or performance for signal morphologies outside the injected family.

The post-audit v15 morphology stress test remains a separate limitation analysis; it is not part of the confirmatory end-to-end benchmark.

## Execution integrity gate
The audit script must refuse to run unless the Git working tree is clean at startup. It records the exact Git commit, benchmark-protocol SHA-256, development-snapshot SHA-256, fixed RF threshold, driver thresholds and event counts in its output. All frozen numerical invariants are asserted before simulation begins.
