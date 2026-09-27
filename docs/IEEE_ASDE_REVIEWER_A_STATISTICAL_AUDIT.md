# Reviewer A — statistical and methodological audit

**Date:** 2026-09-26 (America/Lima)
**Disposition:** **REVIEWER A — DESIGN PASS / PROSPECTIVE CALIBRATION PENDING.** The historical v21/v23 inferential objection remains unresolved as a field-calibration result, but the v24 prospective design has now survived pre-freeze adversarial review, code/protocol concordance, regression tests, source-isolation safeguards, and an inactive-manifest execution barrier. No known pre-freeze design defect remains open at this checkpoint. This is **not** a statistical PASS on field outcomes and does not clear the manuscript for an unconditional calibration claim; the remaining requirement is prospective execution of v24 exactly as frozen later, without using D_validation as a repair set.

## Evidence inspected

- Frozen v21 and v23 protocols and runners; source SHA-256 `eed7df2621f6952b9ea2eaa7524f735a706b69494d3d272fd2dd828b52a97387`.
- v23 row-level `gate_ablation_trials.csv`, `gate_ablation_metrics.csv`, `v23_summary.json`, and reconstruction verifier.
- Partition manifest, adaptive-analysis ledger, holdout-isolation audit, manuscript Draft v1 and claim ledger.
- Post-audit read-only diagnostic `scripts/audit_asde_reviewer_a_shift_orbit.py`; output `Results/scientific_discovery/DISCOVERY-001/reviewer_a_shift_orbit.json`.
- Separately frozen post-audit RF-window observability protocol (`7afefe2`), runner and JSON diagnostic reported below.
- Separately frozen paired-offset observation protocol (`eb25a18`), runner and JSON diagnostic reported below.
- D_validation and external replication cohorts were not opened for this audit.

## Verified counts and comparisons

The v23 CSV has 18,400 rows: four methods × (3,600 injected settings/realizations + 1,000 surrogate-null draws), representing **4,600 paired trial keys**, not 18,400 independent physical observations. Each of the four atmospheric drivers has 23–28 events on the same 2,860-row development snapshot. The 5-min resampling creates 3,276 grid bins, of which 2,858 have all required variables.

Under the registered 1,000 sampled circular shifts, at least one driver was selected 217 times for M0 and 17 times for each of M1, M2, and M3. Selected-driver sets for M1–M3 agreed in all 4,600 paired trials. An independent re-evaluation of the sampled nulls reproduced all 4,000 recorded method-by-seed selected sets exactly (zero mismatches). The 1.0-SD, 60-min exclusive-truth rate under M1 varies by planted driver: 49%, 25%, 2%, and 8% (CU01 temperature rise, SJ01 temperature fall, SJ01 humidity fall, SJ01 pressure rise). The aggregate 21% obscures this heterogeneity.

The post-audit exhaustive diagnostic evaluated all 3,132 offsets allowed by the v23 shift rule on the same fixed background: M0 selected in 649/3,132 (20.72%); M1–M3 in 50/3,132 (1.60%) each; M1–M3 never disagreed. The 1,000-draw rates are thus not an obvious Monte Carlo sampling accident **within this finite shift orbit**. This diagnostic is exploratory and cannot validate the orbit as a scientifically appropriate null.

## New post-audit observability sensitivity

Protocol frozen in commit `7afefe2` before this diagnostic; runner `scripts/audit_asde_reviewer_a_observability.py`; result `Results/scientific_discovery/DISCOVERY-001/reviewer_a_observability.json` (SHA-256 `d482bc1049c08bc2556e503f0b7c33bedac75e070c648c5bf8d06d682de4c8ec`). The same hashed D_development source was used; D_validation and later configuration RF outcomes were not analyzed. This is post-audit sensitivity, not a replacement for v23.

The detector's three-bin RF-quality difference is calculable in only **2,753/3,276** grid bins, fewer than the 2,858 bins with complete contemporaneous RF/weather variables. The original directional test does not require ascertainable RF-detector bins on both sides of a driver event. Under the prospectively stated complete-window policy, the retained driver events by horizon are:

| Driver | 30 min | 60 min | 120 min | Original events |
|---|---:|---:|---:|---:|
| CU01 temperature rise | 16 | 8 | 8 | 23 |
| SJ01 temperature fall | 21 | 6 | 3 | 28 |
| SJ01 humidity fall | 16 | 12 | 3 | 28 |
| SJ01 pressure rise | 17 | 10 | 4 | 28 |

Between 6 and 24 of the original 23–28 driver events per driver/horizon have unequal pre/post observable-bin counts. Requiring complete bilateral windows leaves fewer than eight discordant events in **11/12** original driver–horizon cells, versus **2/12** under v23. None of the four natural-background drivers passes M1 or M3 under either policy, so no natural hypothesis is rescued by the check.

Over all 3,132 historical circular offsets, M1 and M3 select at 50 offsets each under the original rule, but only **4** each under complete-window eligibility. Only **2** selected offsets overlap; the selected set differs at **50** offsets. Across the 37,584 driver–horizon cells of this orbit, the count below eight discordant events rises from **6,856** to **33,350**. The lower selection rate is inseparable from severe event-support loss; it is **not** evidence that the complete-window rule improves field Type-I control. This comparison also does not prove that the original test is anti-conservative: missingness and true event occurrence may be dependent. The new finding is that ascertainment and effective support materially change the benchmark operating point.

The diagnostic checks the calculability of RF-drop differences inside each event window. It does not fully model detector refractory-state history, adaptive threshold selection, or missingness mechanisms. A valid repair would specify the observation policy *before* a new evaluation, retain adequate event support, and calibrate the directional null on independently justified physical temporal blocks. Historical v23 results remain unchanged and conditional on their original policy.

## Paired-offset observation sensitivity

The alternative observation rule was frozen at commit `eb25a18` before execution. It requires finite RF detector differences at matched pre/post offsets and at least half the horizon's offsets paired. Runner: `scripts/audit_asde_reviewer_a_paired_observation.py`; result: `Results/scientific_discovery/DISCOVERY-001/reviewer_a_paired_observation.json` (SHA-256 `12ea0b2f5ec5dfede22145cae6e102338dde59a2fde841cccb6216025aa12de4`). It uses the same development background and historical injection seeds, so is a post-audit sensitivity, not independent replication.

This rule retains **20–28** driver events per driver/horizon, versus **3–21** under the strict complete-window rule. It has fewer than eight discordant events in **3/12** natural-background cells, versus 11/12 with complete windows and 2/12 historically. No natural-background driver is selected by M1/M2/M3 under either the original or paired policy.

| Metric | Historical | Paired observation |
|---|---:|---:|
| M1/M2/M3 selected circular offsets, each / 3,132 | 50 | 47 |
| Shared selected offsets | — | 22 |
| Offsets with changed selected-driver sets | — | 53 |
| Shifted driver–horizon cells below eight discordants / 37,584 | 6,856 | 9,029 |
| 1.0-unit exact/exclusive planted truth, 15 min / 400 | 0.8500 | 0.8075 |
| 1.0-unit exact/exclusive planted truth, 30 min / 400 | 0.8175 | 0.7450 |
| 1.0-unit exact/exclusive planted truth, 60 min / 400 | 0.2100 | 0.0950 |

The rerun reproduces the v23 historical M1/M3 injected rates of 0.8500/0.8175/0.2100 exactly. No distractor co-selection was observed in either of these post-audit 1.0-unit pooled cells. The paired rule addresses one concrete asymmetry in observation opportunity while preserving much more support than complete windows. Its nearly unchanged *aggregate* shift-orbit rate masks 53 changed decisions, and the substantial 60-min recovery loss is a real trade-off in this reused-seed diagnostic. None of these values calibrates the binomial null: serial dependence, weather/RF nonstationarity, detector refractory-state history and physical null validity remain unresolved.

**Method decision:** retain v23 as historical conditional evidence; retain the paired rule as a candidate for a new prospectively frozen audit, not an adopted confirmatory replacement. Before new inference, define observation policy and null episodes independently of outcomes, collect enough eligible events per horizon/episode, and test calibration at the physical-block level. D_validation is not a repair set.

## Objection disposition

| Objection | Severity at review | Resolution / residual boundary |
|---|---|---|
| Pseudoreplication from 18,400 trials | Major | Corrected unit language: trials are conditional simulations on one background; event counts and physical-link count reported. Physical uncertainty remains unestimated. |
| Multiplicity attribution | Major | Confirmed: M0→M1 accounts for the observed change; M2/M3 add no selection benefit in 4,600 paired trials or the complete shift orbit. Full-stack efficacy claim prohibited. |
| Circular-shift null validity | Major; fatal to an unconditional FWER claim | Reframed as surrogate-null selection rate. Gaps, wraparound, nonstationarity, and pre/post asymmetry are not ruled out. No field-wide Type-I guarantee authorized. |
| Binomial directional-test assumptions | Major | 360-min refractory spacing mitigates local repeats but does not prove independent, symmetric discordant events. Bonferroni is conditional on valid constituent p-values. |
| RF observation eligibility | **Major, newly quantified** | The original test counts atmospheric events with incompletely observed pre/post RF windows. A strict complete-window sensitivity changes M1/M3 orbit selections 50→4 while collapsing support. A paired-offset rule retains support and changes the orbit to 47 selections, but only 22 offsets overlap and 60-min planted-truth recovery drops 0.210→0.095. Neither post-hoc alternative may replace v23 or establish field calibration. |
| Wilson interval interpretation | Major | Manuscript now labels intervals conditional Monte Carlo; no between-episode/link confidence claim. |
| Adaptive library selection and v21/v23 reuse | Major | Ledger records development reuse; post-freeze seeds test a frozen library on the same physical background. Both audits remain conditional; no external-replication claim. |
| Weak long-lag and driver-specific power | Major | Results stratified; 1.0-SD/60-min rates can be as low as 2%. Aggregate recovery is not a universal detection claim. |
| Leakage from D_validation | No demonstrated issue | Audit records analytic isolation and runner source hash; this does not assert raw bytes were never historically seen. Holdout remains unopened here. |
| AI incremental benefit | Outside Reviewer A; pending | No statistical or title-level benefit claimed from the unfinished blinded pilot. |

## Closure criteria

A statistical **PASS** requires a prespecified RF-window observation policy with adequate event support, an independently justified null, and dependence-aware calibration of the directional test on suitable physical temporal blocks, with uncertainty at the block/episode level. A narrower Methods paper may instead be evaluated on conditional benchmark operating characteristics after an explicit scope decision and renewed adversarial review; that route accepts a disclosed limitation and **does not convert Reviewer A into a statistical PASS**. Until calibration is demonstrated, the inferential objection remains **OPEN (Major)**.

## Authorized conclusion

ASDE's finite, frozen four-driver benchmark on one real development background exhibits substantially lower *circular-shift surrogate-null selection* after Bonferroni correction (sampled 21.7%→1.7%; exhaustive orbit 20.72%→1.60%). The minimum-support and fold-direction gates do not change selection in this audit. Under registered joint RF injections, recovery is heterogeneous and degrades at longer lags. These are conditional operating characteristics of a bounded synthetic-ground-truth benchmark, not proof of natural environmental causation or calibrated error control in future field periods.

## Remaining scientific gate

A stronger inferential claim requires a prespecified null family representing independently adjudicated stable field episodes, a dependence-aware calibration study for the directional statistic, uncertainty grouped by physical episode/block, and a prospectively protected temporal or external cohort. Do not tune the current analysis against D_validation to achieve this. If no candidate warrants opening D_validation, retain the Methods-paper scope above.

## Reproduction

Run the frozen v23 verifier, then the separate post-audit diagnostics:

```bash
python3 scripts/verify_discovery_001_v23_audit.py
python3 scripts/audit_asde_reviewer_a_shift_orbit.py
python3 scripts/audit_asde_reviewer_a_observability.py
python3 scripts/audit_asde_reviewer_a_paired_observation.py
```

Each diagnostic writes only its own JSON output. It does not change the frozen v23 artifacts.


## v24 pre-freeze design-closure update

Checkpoint: `a3098dd` — **harden Reviewer A v24 prefreeze calibration design**.  
Follow-up repository hygiene: `24a1f04` — preserves the earlier metadata-readiness helper as a hash-pinned historical tool rather than silently retargeting it to the live export.

The v24 prospective design now includes:

- fixed 7000 MHz / 20 MHz primary configuration and frozen RF/weather normalization constants;
- immutable 60-calendar-day prospective window after `CALIBRATION_START_UTC`;
- matched-offset RF observation policy fixed before future outcomes;
- joint daily weather-profile sham generator plus prespecified 48-h dependence sensitivity;
- strict A -> B temporal ordering: first 30 days calibrate, next 30 evaluate;
- A1 cellwise empirical calibration and independent A2 family-wise min-p calibration;
- fixed 12-cell family with support-ineligible cells retained as nonselectable rather than dropped;
- 0.04 preregistered operating cutoff with external conditional-calibration ceiling 0.05;
- 2500 A1, 2500 A2 and 5000 B-test schedules with disjoint seed families;
- explicit separation of randomized-sham N1 calibration from natural-weather N2 claims;
- natural-driver RF scores sealed until N1 disposition;
- machine-readable start-manifest schema and inactive template;
- validator and runner barriers that refuse prospective execution while the manifest remains inactive;
- explicit prohibition of D_validation and historical integrated/prevalidation CSVs as v24 prospective sources.

### Adversarial bugs found and fixed before prospective freeze

**Support-shift bug.** The first A1 implementation retained support-ineligible schedules in the empirical-p denominator. A controlled case with zero eligible A1 references yielded raw p=0.0003998401 and family-wise p=0.0043982407, which would have selected an unsupported cell. The procedure now conditions the cellwise empirical reference on support-eligible A1 schedules; zero-reference cells receive p=1. The same counterexample now returns raw p=1 and family-wise p=1.

**Exact-grid bug.** The first day-eligibility implementation checked only that a day contained 288 rows. A day with one duplicated 5-min timestamp and one missing bin could therefore pass the row-count condition. V24 now requires exact equality to the unique 288-bin America/Lima 5-min grid; a regression test verifies rejection of the duplicate/missing-bin case.

**Adaptive restart risk.** An earlier draft allowed a failed day to be replaced by starting a later clean 60-day run under the same experiment. The final draft prohibits this: once `CALIBRATION_START_UTC` is frozen, the next 60 calendar days are immutable. Any ineligible day makes that experiment `NOT_CALIBRATED`; a retry requires a new experiment ID and a new prospective freeze.

**Invisible-test provenance.** The v24 regression test was initially hidden by the repository rule `test_*.py`. It is now explicitly forced into Git, and the concordance auditor fails if any protected protocol/code/test/manifest/validator/runner artifact is not present in the Git index.

### Current machine-audited status

The pre-freeze concordance artifact reports:

- `status = PASS`;
- four-driver × three-horizon family = 12 cells;
- historical weather-event reproduction = 23 / 28 / 28 / 28;
- historical frozen RF-event reproduction = 158 events;
- template validation = PASS;
- `prospective_execution_authorized = false`;
- inactive-template runner test = REFUSED as required;
- `calibration_start_utc = null`.

Thus no prospective v24 outcome has been inspected or analyzed.

### Reviewer-A status interpretation

**DESIGN PASS** means the current v24 protocol/implementation checkpoint has no known unresolved pre-freeze statistical-design objection from this audit.

It does **not** mean:

- field null calibration has passed;
- natural weather has calibrated Type-I error;
- 60 calendar days are 60 independent physical episodes;
- N1 randomized-sham calibration substitutes for N2 natural negative controls;
- D_validation may be opened;
- v21/v23 historical limitations disappear.

A final statistical PASS remains conditional on executing the future cohort without protocol drift and satisfying the preregistered N1/N2 disposition rules.
