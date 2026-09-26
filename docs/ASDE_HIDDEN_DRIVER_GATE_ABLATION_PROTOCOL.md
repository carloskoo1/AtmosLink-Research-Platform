# ASDE Hidden-Driver Gate Ablation — Frozen Protocol v1

## Purpose
Quantify the incremental operating effect of the statistical safeguards used by the ASDE hidden-driver selector. The experiment compares nested decision rules under the same frozen four-driver hypothesis library, the same RF outcome definition, the same synthetic perturbation family, and the same real AtmosLink development background.

This is a secondary audit of decision rules. It does not retune v21, does not use D_validation, and does not establish open-ended discovery performance.

## Frozen background and hypothesis library
Use the exact DISCOVERY-001 development snapshot and frozen v21 four-driver library:

1. cu01_local_temp_avg_c__rise — threshold 1.5308007671599377; 23 events.
2. sj01_local_temp_avg_c__fall — threshold 1.2876641771825945; 28 events.
3. sj01_local_hum_avg_pct__fall — threshold 1.6365945597866016; 28 events.
4. sj01_local_press_hpa__rise — threshold 0.8993210126363124; 28 events.

Development snapshot SHA-256:
eed7df2621f6952b9ea2eaa7524f735a706b69494d3d272fd2dd828b52a97387

Frozen RF-drop threshold:
-0.5620817932460992

Response horizons:
30, 60, and 120 minutes.

## Nested selector rules
Every driver-horizon pair is evaluated by the same one-sided exact pre/post directional test.

### M0 — uncorrected p-value selector
A driver is selected when at least one horizon satisfies:
- p < 0.05.

No multiplicity correction, minimum-discordant support, or fold-direction gate is applied.

### M1 — family-wise threshold only
A driver is selected when at least one horizon satisfies:
- p < 0.05 / 12.

No minimum-discordant support or fold-direction gate is applied.

### M2 — family-wise threshold + support
A driver is selected when at least one horizon satisfies:
- p < 0.05 / 12;
- at least 8 discordant events.

No fold-direction gate is applied.

### M3 — full ASDE hidden-driver gate
A driver is selected when at least one horizon satisfies:
- p < 0.05 / 12;
- at least 8 discordant events;
- post-event RF entries exceed pre-event RF entries in at least 3 of 4 contiguous development folds.

M3 is identical to the registered v21 statistical gate.

## Synthetic perturbation family
For each injected trial, exactly one frozen driver is the hidden truth.

Effects:
- 0.5, 1.0, and 1.5 robust SD per RF metric.

Lags:
- 15, 30, and 60 minutes.

Duration:
- 15 minutes.

Activation probability:
- 0.70 per eligible true-driver event.

Perturbation:
- joint abrupt degradation across DL/UL RSSI, SNR, and MCS.

## Audit randomization
- 100 independent injection trials per truth-driver × effect-size × lag cell.
- Reserved injection seeds: 420000–420099.
- 1000 library-wide circular-shift null trials.
- Reserved null RNG seed: 2026092607.

The circular shift is applied jointly to all four candidate event sets to preserve cross-driver temporal structure while breaking their relation to the unchanged RF background.

## Primary endpoints by method
For M0, M1, M2, and M3 report:

1. library-wide null family-wise error rate;
2. exact-truth selection rate;
3. exclusive exact-truth selection rate;
4. distractor co-selection rate;
5. mean number of selected drivers.

All proportion estimates use Wilson 95% confidence intervals.

## Primary comparison
The principal comparison is the trade-off between library-wide null FWER and exact-truth recovery across M0–M3.

No method is declared globally superior. A more restrictive rule may reduce false selection while sacrificing sensitivity.

## Claim limits
This audit can quantify the incremental operating behavior of nested decision rules within the frozen v21 finite-library benchmark. It cannot establish:
- universal Type-I error control;
- superiority for arbitrary hypothesis spaces;
- causal correctness of natural atmospheric effects;
- performance for RF morphologies outside the registered joint perturbation family;
- independent external validation.

## Integrity requirements
The runner must:
- refuse execution if the Git working tree is dirty;
- assert the development snapshot hash;
- assert all frozen driver event counts;
- assert pairwise library-overlap constraints;
- assert the frozen RF-drop threshold;
- record the exact Git commit and protocol SHA-256 before simulation.

No rule, threshold, seed, endpoint, or hypothesis-library element may be changed after audit execution.
