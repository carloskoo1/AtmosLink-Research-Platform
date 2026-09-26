# Reviewer A — statistical and methodological audit

**Date:** 2026-09-26 (America/Lima)
**Disposition:** CLOSED for a **bounded Methods-paper claim** after corrections below. This is not approval of field-wide Type-I control, natural atmospheric causality, cross-link generalization, or submission readiness.

## Evidence inspected

- Frozen v21 and v23 protocols and runners; source SHA-256 `eed7df2621f6952b9ea2eaa7524f735a706b69494d3d272fd2dd828b52a97387`.
- v23 row-level `gate_ablation_trials.csv`, `gate_ablation_metrics.csv`, `v23_summary.json`, and reconstruction verifier.
- Partition manifest, adaptive-analysis ledger, holdout-isolation audit, manuscript Draft v1 and claim ledger.
- Post-audit read-only diagnostic `scripts/audit_asde_reviewer_a_shift_orbit.py`; output `Results/scientific_discovery/DISCOVERY-001/reviewer_a_shift_orbit.json`.
- D_validation and external replication cohorts were not opened for this audit.

## Verified counts and comparisons

The v23 CSV has 18,400 rows: four methods × (3,600 injected settings/realizations + 1,000 surrogate-null draws), representing **4,600 paired trial keys**, not 18,400 independent physical observations. Each of the four atmospheric drivers has 23–28 events on the same 2,860-row development snapshot. The 5-min resampling creates 3,276 grid bins, of which 2,858 have all required variables.

Under the registered 1,000 sampled circular shifts, at least one driver was selected 217 times for M0 and 17 times for each of M1, M2, and M3. Selected-driver sets for M1–M3 agreed in all 4,600 paired trials. The 1.0-SD, 60-min exclusive-truth rate under M1 varies by planted driver: 49%, 25%, 2%, and 8% (CU01 temperature rise, SJ01 temperature fall, SJ01 humidity fall, SJ01 pressure rise). The aggregate 21% obscures this heterogeneity.

The post-audit exhaustive diagnostic evaluated all 3,132 offsets allowed by the v23 shift rule on the same fixed background: M0 selected in 649/3,132 (20.72%); M1–M3 in 50/3,132 (1.60%) each; M1–M3 never disagreed. The 1,000-draw rates are thus not an obvious Monte Carlo sampling accident **within this finite shift orbit**. This diagnostic is exploratory and cannot validate the orbit as a scientifically appropriate null.

## Objection disposition

| Objection | Severity at review | Resolution / residual boundary |
|---|---|---|
| Pseudoreplication from 18,400 trials | Major | Corrected unit language: trials are conditional simulations on one background; event counts and physical-link count reported. Physical uncertainty remains unestimated. |
| Multiplicity attribution | Major | Confirmed: M0→M1 accounts for the observed change; M2/M3 add no selection benefit in 4,600 paired trials or the complete shift orbit. Full-stack efficacy claim prohibited. |
| Circular-shift null validity | Major; fatal to an unconditional FWER claim | Reframed as surrogate-null selection rate. Gaps, wraparound, nonstationarity, and pre/post asymmetry are not ruled out. No field-wide Type-I guarantee authorized. |
| Binomial directional-test assumptions | Major | 360-min refractory spacing mitigates local repeats but does not prove independent, symmetric discordant events. Bonferroni is conditional on valid constituent p-values. |
| Wilson interval interpretation | Major | Manuscript now labels intervals conditional Monte Carlo; no between-episode/link confidence claim. |
| Adaptive library selection and v21/v23 reuse | Major | Ledger records development reuse; post-freeze seeds test a frozen library on the same physical background. Both audits remain conditional; no external-replication claim. |
| Weak long-lag and driver-specific power | Major | Results stratified; 1.0-SD/60-min rates can be as low as 2%. Aggregate recovery is not a universal detection claim. |
| Leakage from D_validation | No demonstrated issue | Audit records analytic isolation and runner source hash; this does not assert raw bytes were never historically seen. Holdout remains unopened here. |
| AI incremental benefit | Outside Reviewer A; pending | No statistical or title-level benefit claimed from the unfinished blinded pilot. |

## Authorized conclusion

ASDE's finite, frozen four-driver benchmark on one real development background exhibits substantially lower *circular-shift surrogate-null selection* after Bonferroni correction (sampled 21.7%→1.7%; exhaustive orbit 20.72%→1.60%). The minimum-support and fold-direction gates do not change selection in this audit. Under registered joint RF injections, recovery is heterogeneous and degrades at longer lags. These are conditional operating characteristics of a bounded synthetic-ground-truth benchmark, not proof of natural environmental causation or calibrated error control in future field periods.

## Remaining scientific gate

A stronger inferential claim requires a prespecified null family representing independently adjudicated stable field episodes, a dependence-aware calibration study for the directional statistic, uncertainty grouped by physical episode/block, and a prospectively protected temporal or external cohort. Do not tune the current analysis against D_validation to achieve this. If no candidate warrants opening D_validation, retain the Methods-paper scope above.

## Reproduction

Run the frozen v23 verifier, then the separate post-audit diagnostic:

```bash
python3 scripts/verify_discovery_001_v23_audit.py
python3 scripts/audit_asde_reviewer_a_shift_orbit.py
```

The diagnostic writes only its own JSON output. It does not change the frozen v23 artifacts.
