# Reviewer A — v24 prospective physical-null calibration protocol

**Status:** DRAFT — VERSIONABLE, NOT FROZEN — DO NOT EXECUTE.  
**Relationship to prior work:** this protocol does not replace v21, v23, the complete-window sensitivity, the paired-offset sensitivity, or the physical-null readiness gate in `ASDE_REVIEWER_A_PHYSICAL_NULL_PROTOCOL.md`. It defines a prospective calibration study that may begin only after a later explicit freeze commit and CALIBRATION_START_UTC.

## 1. Primary objective

Evaluate whether the frozen ASDE directional-selection procedure is calibrated on **new, prospectively collected field data** when RF observation opportunity, temporal dependence, multiplicity, and local diurnal structure are handled by rules fixed before the first included outcome.

The primary target is a bounded Methods-paper statement about conditional field operating characteristics. The protocol does **not** attempt to prove natural atmospheric causality or a universal future Type-I error guarantee.

## 2. Historical evidence is development evidence

The following findings motivate v24 but cannot confirm it:

- v23 showed strong sensitivity of hidden-driver selection to multiplicity control;
- complete-window eligibility demonstrated severe support loss;
- the paired-offset rule retained 20–28 driver events per cell but changed 53 shift-orbit decisions and reduced 1.0-unit 60-min recovery from 0.210 to 0.095;
- development-only autocorrelation diagnostics showed strong raw diurnal structure; after removal of the 5-min slot-of-day mean, 15-min weather/RF difference signals had small residual correlations at the inspected 12–48 h lags;
- event-count dependence was materially stronger in 12-h blocks than in 24-h blocks for several frozen drivers.

These observations make every v24 choice **development-informed**. Confirmatory status begins only on a future cohort collected after the freeze.

## 3. Two distinct null estimands

### N1 — randomized sham-schedule null
Sham atmospheric-event schedules are generated without consulting RF outcomes. Conditional on eligible times and the fixed scheduling design, this tests the selector against a real RF background when exposure timing is randomized by design.

N1 supports statements about **algorithmic false selection under the registered sham design**.

### N2 — natural-weather null
Natural atmospheric events are not randomly assigned. A natural negative-control exposure requires independent physical justification that the exposure should have no directional RF effect under the study conditions.

N2 is required for stronger statements about natural-weather false selection.

**No N1 result may be automatically reinterpreted as N2 calibration.**

## 4. Prospective data boundary

Before the first included sample, freeze a machine-readable start manifest containing:

- `CALIBRATION_START_UTC`;
- Git commit and protocol SHA-256;
- station, firmware, QC and timestamp configuration;
- radio frequency, bandwidth, AP/SM power and association requirements;
- maintenance/outage exclusion rules;
- observation policy;
- block definition;
- local-time matching rule;
- sham RNG seed family;
- test family and multiplicity procedure.

Primary v24 data must occur strictly after `CALIBRATION_START_UTC`.

The primary v24 radio configuration is fixed to **7000 MHz center frequency / 20 MHz channel bandwidth**, matching the DISCOVERY-001 development configuration from which the RF outcome detector was frozen. A different frequency or bandwidth cannot be substituted into v24. It requires a separately preregistered detector and a different experiment identifier.

The start manifest must also freeze AP/SM transmit-power settings, TDD/frame settings, firmware/configuration identifiers and dual-association requirements. Any change during the 60-day run breaks cohort continuity.

Excluded from v24 primary calibration:

- D_validation;
- DISCOVERY-001 development rows;
- all v21/v23/post-audit sensitivity rows;
- any interval used to choose or revise v24 rules;
- configuration transitions, recovery incidents, timestamp ambiguity, or QC-failed intervals.

A configuration change terminates the current eligible segment; configurations may not be concatenated to manufacture continuity.

## 5. Readiness gate inherited from the physical-null specification

Before RF/weather outcomes of a candidate future segment are used for v24 calibration, the metadata-only readiness gate must pass.

The existing readiness specification remains separate and necessary but not sufficient. Passing it does not imply statistical calibration.

### 5A. Frozen local-day eligibility rule

Day eligibility is determined without using RF magnitude or RF-event outcomes.

For each America/Lima local calendar day, construct the expected 288-bin 5-min grid.

A day is eligible only when all are true:

1. the frozen primary radio configuration is 7000 MHz / 20 MHz for the entire day;
2. AP transmit power is 10 dBm and SM transmit power is 3 dBm for every available configuration record;
3. collection status is `LINK_OPERATIONAL_DUAL` for every available operational-status record;
4. `tdd_dl_pct`, `tdd_ul_pct` and `tdd_frame_ms` match the exact non-null values recorded in the future CALIBRATION_START manifest throughout the day;
5. no maintenance, outage, recovery incident or configuration-transition exclusion overlaps the day;
6. at least 274/288 bins (>=95%) have the required operational metadata available and matching the frozen regime;
7. at least 274/288 bins (>=95%) pass the frozen weather-QC eligibility for all four atmospheric driver variables.

RF RSSI, SNR, MCS, RF-drop status and RF numerical availability are **not** part of day eligibility.

A day that fails any criterion makes the preregistered v24 cohort **NOT_CALIBRATED**. It cannot be deleted, replaced, or used to shift the cohort start. After CALIBRATION_START_UTC, the 60 calendar days are immutable. Any later retry requires a new experiment identifier, a new prospective start manifest, and a new freeze before its first included sample.

The weather-QC implementation/version and operational-metadata field definitions must be hashed in the CALIBRATION_START manifest.

## 6. Primary observation rule

The primary v24 observation policy is the **matched-offset rule** developed in commit `eb25a18`, applied unchanged to the new cohort:

For atmospheric anchor bin e and one-sided horizon h in {6, 12, 24} five-minute bins:

- offset k is usable only when RF detector ascertainability holds at both e-k and e+k;
- only matched offsets contribute to pre/post classification;
- out-of-grid offsets are ineligible;
- an event is analyzable only when at least ceil(h/2) matched offsets are usable.

The >=50% rule is development-informed and therefore cannot retroactively validate historical results. It is fixed prospectively only for v24.

The strict complete-window rule is retained as a **secondary, prespecified sensitivity** and cannot replace the primary rule after results are known.

## 6A. Frozen RF outcome definition

V24 inherits the v23 six-field RF composite without recalibration on prospective data.

Feature order:

1. dl_rssi_dbm
2. ul_rssi_dbm
3. dl_snr_db
4. ul_snr_db
5. dl_mcs
6. ul_mcs

Frozen D_development robust centers:

- dl_rssi_dbm = -74.0
- ul_rssi_dbm = -80.0
- dl_snr_db = 23.0
- ul_snr_db = 18.0
- dl_mcs = 204.0
- ul_mcs = 202.0

Frozen robust scales:

- dl_rssi_dbm = 0.7412898443291327
- ul_rssi_dbm = 0.7412898443291327
- dl_snr_db = 0.7412898443291327
- ul_snr_db = 1.4826
- dl_mcs = 5.896045450988336
- ul_mcs = 1.4826

Frozen RF-drop threshold:

`-0.5620817932460992`

These values are copied from the hashed D_development/v23 definition. They may not be recomputed, updated, normalized or re-estimated from Fold A or Fold B.

RF ascertainability may depend on whether the required prospective RF fields are finite, but event magnitude and threshold remain frozen.

## 7. Primary physical time unit

The primary block is one **local calendar day in America/Lima (UTC-05:00)**.

Rationale from development-only diagnostics:

- 12-h event-count blocks retained substantial lag-1 dependence for several frozen drivers;
- 24-h blocks showed materially smaller lag-1 event-count correlations;
- raw weather variables have strong diurnal structure;
- residualized 15-min difference signals were much less dependent after controlling for time of day.

This does not prove day-level independence. A 24-h day is the **primary clustering unit**, not an assertion that adjacent days are IID.

A 48-h block analysis is prespecified as a dependence-sensitivity check.

## 8. Minimum prospective volume

The primary cohort requires one continuous run of:

- **60 consecutive local calendar days** under one fixed v24-eligible radio configuration;
- each local day individually satisfying the frozen day-eligibility/metadata criteria;
- no day skipped to bridge an outage, maintenance interval, configuration change or ineligible regime.

This corresponds to a 1440-h calendar span. Minor missing samples are handled only through the frozen day-eligibility and matched-offset rules; days themselves are not removed and concatenated.

If any local day fails the frozen eligibility rule, the preregistered 60-day cohort is not patched by omission and is labeled NOT_CALIBRATED. The same experiment identifier cannot restart from a later day.

The 60-day requirement is a **necessary volume/continuity gate, not a claim of 60 independent physical episodes**.

After the first 30 consecutive eligible days (720 h of calendar span), v24 may issue a blinded/readiness interim report limited to:

- metadata completeness;
- number of eligible days;
- observation-policy coverage;
- counts of candidate anchors by local-time stratum;
- QC/exclusion counts.

No RF-selection rate, p-value, threshold tuning, or rule revision is permitted at the 720-h checkpoint.

The 1440-h gate authorizes the prespecified calibration analysis only if all other readiness conditions pass.

## 9. Frozen hypothesis family

Primary v24 calibration is restricted to the same four atmospheric event definitions used in the hidden-driver audit:

1. CU01 temperature rise;
2. SJ01 temperature fall;
3. SJ01 relative-humidity fall;
4. SJ01 pressure rise.

Their numerical event thresholds and 360-min refractory rule must be copied exactly from the frozen v21/v23 library into the final start manifest.

Primary horizons remain 30, 60, and 120 min.

Therefore the primary family contains 4 × 3 = 12 driver-horizon cells.

No fifth driver, alternative threshold, new horizon, or revised refractory interval may enter the primary v24 analysis after CALIBRATION_START_UTC.

### 9A. Frozen atmospheric-event normalization

Prospective v24 event detection must **not** recompute robust centers/scales from Fold A or Fold B.

Frozen D_development 15-min difference references:

| Driver variable | diff15 median | robust scale | frozen z-direction threshold | equivalent physical 15-min threshold |
|---|---:|---:|---:|---:|
| CU01 temperature | -0.07000000000000028 °C | 0.34099799999999536 | z >= 1.5308007671599377 | Δ15 >= +0.452 °C |
| SJ01 temperature | -0.020000000000000462 °C | 0.3261719999999983 | z <= -1.2876641771825945 | Δ15 <= -0.440 °C |
| SJ01 relative humidity | 0.0 pp | 1.5715560000000033 | z <= -1.6365945597866016 | Δ15 <= -2.572 pp |
| SJ01 pressure | 0.009999999999990905 hPa | 0.13343399999987862 | z >= 0.8993210126363124 | Δ15 >= +0.130 hPa |

The physical thresholds above are algebraically equivalent to the frozen robust-z rules and are included for auditability. The implementation must use the frozen constants, not future-distribution normalization.

Peak selection remains the frozen local-maximum rule with the 360-min same-driver refractory interval.

## 10. Primary N1 sham generator: joint daily-profile permutation

All timestamps are converted to America/Lima local civil time before sham generation.

For each prospective fold, construct one **joint multivariate daily event profile** per eligible local day. A daily profile contains the exact local hour and minute of every frozen-driver atmospheric event occurring on that day, preserving driver identity.

The primary N1 sham generator is:

1. draw a uniformly random permutation of the eligible local-day labels;
2. apply the **same permutation jointly to all four driver profiles**;
3. move every event in a source-day profile to the target day while preserving its exact local hour and minute;
4. reject any permutation with a fixed day profile (full derangement requirement);
5. reject any permutation that produces a <360-min gap between consecutive sham events of the same driver;
6. otherwise accept the joint sham schedule.

The accepted schedule therefore preserves exactly:

- total event count for every driver;
- exact local time-of-day distribution;
- within-day event geometry;
- within-day cross-driver co-occurrence;
- driver identity.

It deliberately randomizes which physical RF day receives each joint weather-event profile.

No RF numerical value, RF-event outcome or RF-availability field may be consulted when proposing or accepting the permutation. The matched-offset RF observation rule is applied **after** the sham schedule exists, identically to sham and real atmospheric anchors.

N1 does not require sham profiles to avoid real atmospheric events on the target day. Such overlap belongs to the real physical background and is reported as a diagnostic. N1 remains a randomized-label calibration, not a natural no-weather null.

The uniform day-profile permutation **defines an artificial conditional null by design**. V24 does not assume or claim that naturally observed weather-day labels are exchangeable in a causal or physical sense. The A -> B evaluation asks only whether a procedure calibrated under the frozen Fold-A sham generator maintains its registered conditional false-selection behavior on a later physical RF background under the same sham-generating rule. The 48-h analysis probes sensitivity to the chosen temporal unit but does not prove natural-day exchangeability.

Accepted permutations are sampled **with replacement** from the rejection sampler. Repeated schedules are permitted and their frequency is reported; this preserves a well-defined IID Monte Carlo sampling interpretation conditional on the fold.

Pre-freeze feasibility evidence:
- a weather/time-only diagnostic on seven complete D_development local days proposed 20,000 joint derangements;
- 3,190 satisfied the joint refractory rule (acceptance fraction 0.1595);
- no RF columns or D_validation were read.

Artifact: `reviewer_a_v24_day_profile_feasibility.json`.

A secondary 48-h generator groups adjacent eligible days into fixed non-overlapping 48-h joint profiles and applies the analogous derangement/refractory procedure at the 48-h-profile level.

The earlier 1-h/2-h individual-anchor feasibility diagnostic is retained as development evidence but is not the primary v24 sham generator.

## 11. Primary directional statistic

For each driver-horizon cell define:

- P = number of analyzable atmospheric events classified post-only;
- R = number classified pre-only;
- D = P + R;
- T = P - R.

The primary standardized score is:

S = T / sqrt(max(D,1)).

This standardization is fixed before prospective execution. It does not assert a Binomial(0.5) model.

A cell is inferentially eligible only when:

- D >= 8; and
- discordant events occur on at least 4 distinct local-day blocks.

Cells failing either requirement are reported descriptively and cannot be selected.

The historical one-sided binomial p-value and the historical fold-direction count are secondary diagnostics only.

## 12. Cellwise empirical calibration and family-wise adjustment

The primary procedure does not assume that S has the same null scale across drivers or horizons.

Fold A sham schedules are divided **before execution** into two disjoint seed families:

- A1: 2500 sham schedules for cellwise empirical calibration;
- A2: 2500 sham schedules for family-wise calibration.

For every cell j, let m_j be the number of A1 sham schedules in which that cell satisfies the frozen support-eligibility rule. For an **eligible** target score s, define the A1 empirical one-sided tail probability conditional on cellwise support eligibility:

p_j(s) = (1 + number of support-eligible A1 sham scores S_j >= s) / (m_j + 1).

If the target cell is support-ineligible, assign p_j = 1. If m_j = 0, also assign p_j = 1; a cell with no eligible A1 reference is therefore nonselectable rather than spuriously extreme.

This conditioning is required because support eligibility can vary across sham schedules. Ineligible A1 schedules do not enter the numerical score reference for that cell.

For every A2 sham schedule r:

1. compute p_j for all inferentially eligible cells using only the cell's support-eligible A1 reference schedules;
2. assign p_j = 1 to every support-ineligible cell, and to any cell with m_j = 0, so the registered family always contains exactly 12 cells;
3. define U_r = minimum p_j across the fixed 12-cell family;
4. retain U_r, the full vector of p_j values, m_j, and every cell's support state.

The family size never shrinks schedule by schedule.

For a new score s* in cell j, first compute p_j(s*) from A1. Then define its family-wise adjusted empirical p-value:

p_FWER,j = (1 + number of A2 schedules with U_r <= p_j(s*)) / (2500 + 1).

A primary cell is selected only when:

- p_FWER,j <= **0.04**; and
- its support eligibility rule is satisfied.

The 0.04 value is a **pre-freeze operating cutoff**, not the claimed calibration level and not a post-result correction. The external conditional-calibration ceiling remains 0.05. With 5000 held-out sham schedules, the pass boundary is 224 selections: 224/5000 = 0.0448 has a one-sided 95% Clopper-Pearson upper bound of approximately 0.049913, whereas 225/5000 exceeds 0.05. Under a Binomial design calculation used only for planning the Monte Carlo audit, a true conditional selection probability of 0.05 has approximately 0.0472 probability of satisfying K<=224, while a true rate of 0.04 has approximately 0.9596 probability. The 0.04 cutoff is therefore an intentionally conservative operating margin chosen before prospective execution; it is not evidence that the natural-weather Type-I error is 4%.

This nested empirical procedure allows the 12 cells to have different null scales while using their joint A2 distribution for family-wise adjustment.

Bonferroni over the historical binomial p-values is retained only as a prespecified comparator to v23.

## 13. Prospective calibration and held-out evaluation

After 60 eligible local days are accrued, partition them chronologically into:

- **Fold A:** first 30 eligible local days — calibration only;
- **Fold B:** next 30 eligible local days — held-out evaluation only.

No RF inferential result from either fold may be inspected before both folds are complete.

No day may move between folds after CALIBRATION_START_UTC.

For each fold:

- identify frozen-driver atmospheric events using weather/QC only;
- construct joint daily profiles exactly as specified in Section 10;
- generate accepted sham schedules by uniform random day-label permutation with rejection;
- never consult RF outcomes or RF availability during proposal/acceptance.

Frozen primary seed families:

- A1 seed = 2026092601;
- A2 seed = 2026092602;
- B-test seed = 2026092603.

Required accepted schedules:

- A1 = 2500;
- A2 = 2500;
- B-test = 5000.

Each seed family may examine at most **1,000,000 permutation proposals**. If the required accepted count is not reached within that cap, v24 is NOT CALIBRATED. The generator, cap or acceptance constraints may not be changed on the same cohort.

Primary direction:

1. A1 and A2 are generated on Fold A and define the complete calibration procedure;
2. 5000 independent accepted B-test sham schedules are generated on Fold B;
3. each B-test schedule is scored using A1/A2 only;
4. a B-test schedule is counted as a family-wise false selection if any registered cell has p_FWER <= 0.04.

The **Fold A -> Fold B** sham-selection rate is the sole primary N1 endpoint.

A reverse B -> A analysis may be preregistered as a secondary transport diagnostic using fully disjoint sham seed families. It is not pooled with the primary endpoint and cannot rescue a failed A -> B result.

Repeated sham schedules on one RF fold are **Monte Carlo replicates conditional on that physical RF background**, not independent field episodes. Report this explicitly.

## 14. Physical-block dependence reporting

The local day is the primary clustering unit.

Report, for each frozen driver and fold:

- number of eligible days;
- number of days containing at least one driver event;
- distribution of event counts per day;
- lag-1 correlation of daily event counts when estimable;
- support days contributing discordant events.

Repeat the full N1 procedure with **joint non-overlapping 48-h profiles**:

- Fold A contains 15 ordered 48-h profiles;
- Fold B contains 15 ordered 48-h profiles;
- the same four-driver event profiles within each 48-h unit are permuted jointly;
- full derangement and same-driver 360-min refractory constraints remain;
- separate seeds 2026092604 / 2026092605 / 2026092606 are used for 48-h A1 / A2 / B-test;
- required accepted counts and the 1,000,000-proposal cap are identical to the 24-h primary analysis.

The 48-h result is a prespecified dependence-sensitivity gate, not an alternative result chosen after inspection.

## 15. N1 primary endpoint

Primary endpoint:

**Fold A -> Fold B randomized-sham family-wise selection rate** under the frozen nested empirical calibration procedure.

Report:

- number of A1, A2 and B-test sham schedules;
- Fold B family-wise selection count and rate;
- conditional Monte Carlo interval for the B-test sham rate;
- support/ineligibility counts by driver-horizon cell;
- 24-h primary and 48-h dependence-sensitivity results;
- any secondary B -> A transport diagnostic separately, never pooled with the primary endpoint.

The B-test sham count is a Monte Carlo denominator, not a count of independent field episodes.

For the 24-h primary and 48-h sensitivity analyses separately, compute the **one-sided 95% Clopper-Pearson upper confidence bound** for the conditional B-test sham-selection probability.

The conditional calibration criterion is satisfied only when:

- the observed B-test family-wise selection rate is <= 0.05; and
- its one-sided 95% Clopper-Pearson upper bound is <= 0.05.

With n = 5000 B-test sham schedules, this requires at most **224 selected schedules** (224/5000 = 0.0448; one-sided 95% Clopper-Pearson upper bound approximately 0.04991). At 225/5000 the upper bound exceeds 0.05.

Both the 24-h and 48-h procedures must satisfy this criterion for Conditional N1 PASS.

This endpoint is **not** a universal Type-I error rate for natural weather events. The Clopper-Pearson interval quantifies Monte Carlo uncertainty under the frozen sham generator; it does not quantify between-episode, between-season or between-link uncertainty.

## 16. N2 natural-negative-control requirement

A full natural-weather calibration claim requires a separate, pre-frozen N2 specification naming one or more atmospheric negative-control exposures and their physical justification **without reference to RF outcomes**.

N2 must specify:

- why the exposure is expected not to cause the registered RF degradation process;
- event detector and thresholds;
- local-time matching;
- expected support;
- physical episode/block structure;
- multiplicity family.

If no defensible N2 exposure can be specified prospectively, v24 may support only an **N1 conditional algorithmic-calibration statement**.

Absence of N2 is not repaired by more sham schedules.

## 17. Separation from natural-driver testing

The primary v24 calibration phase does **not** inspect or report RF selection for the actual prospective atmospheric-driver events in Fold B.

Those natural events may be used from weather/QC only to define event counts, local-hour histograms and sham matching. Their RF directional scores remain sealed until:

1. the N1 calibration analysis is complete;
2. all v24 outputs and disposition are immutable; and
3. a separate natural-driver analysis plan is preregistered.

This prevents the calibration study from being influenced by whether the real atmospheric candidates appear favorable.

## 18. Prospective planted-signal operating characteristics

Synthetic RF perturbations on the new prospective background may be evaluated only **after the N1 calibration result and Reviewer-A conditional disposition are finalized and immutable**. They are not permitted to influence N1 calibration, sham generation, support rules or multiplicity thresholds.

Primary perturbation family remains the registered v23 joint abrupt RF degradation unless changed before CALIBRATION_START_UTC.

Report:

- exact truth selection;
- exclusive truth selection;
- distractor co-selection;
- abstention;
- results by driver and lag, not only pooled.

These are conditional sensitivity measurements on the new background and do not establish natural causality.

## 19. Interim 720-h checkpoint

At 30 eligible days / 720 eligible hours, generate a **blinded readiness report only**.

Allowed fields:

- metadata coverage;
- eligible/ineligible day counts;
- maintenance/QC exclusions;
- weather-event counts and complete daily profiles by driver;
- matched-offset availability;
- support geometry not involving RF-event classifications.

Forbidden at interim:

- RF directional statistics;
- RF-drop selection rate;
- max-statistic thresholds;
- binomial p-values;
- sham-selection outcomes;
- modification of observation, support, time-stratum, block or multiplicity rules.

The interim report cannot authorize protocol changes on the same cohort.

## 20. Reviewer-A disposition rule

### Conditional N1 PASS
Reviewer A may be changed from OPEN to **CONDITIONAL PASS — randomized-sham calibration only** when all are true:

1. >=60 eligible local days / >=1440 eligible hours are accrued prospectively under the frozen v24 rules;
2. D_validation remains unused;
3. primary observation/local-time/sham/block rules were frozen before the first included sample;
4. the primary A -> B calibration/evaluation executes without post-hoc repair;
5. support and dependence diagnostics are reported;
6. both the 24-h primary and 48-h sensitivity B-test rates satisfy the prespecified Clopper-Pearson conditional calibration criterion;
7. the prospective natural-driver RF scores remained sealed through completion of N1 calibration;
8. all claims remain explicitly conditional on the registered sham design and physical background.

### Full Reviewer-A PASS
A full PASS additionally requires either:

- prospectively justified N2 natural negative controls with dependence-aware calibration; or
- genuinely external physical replication sufficient to support the stronger inferential scope.

N1 alone cannot be relabeled as natural-weather Type-I calibration.

## 21. Failure / stop rules

### NOT_CALIBRATED — integrity/design failure
v24 is labeled `NOT_CALIBRATED` if any of the following occurs:

- fewer than 60 eligible local-day blocks;
- protocol or inferential code changed after CALIBRATION_START_UTC;
- RF values, RF events or RF availability used to propose/accept sham permutations;
- a required A1/A2/B-test sham family does not reach its accepted-schedule target within 1,000,000 proposals;
- configuration segments are concatenated across incompatible regimes;
- primary support rule is lowered after inspection;
- Fold A/B membership is changed after outcome access;
- prospective natural-driver RF scores are unsealed before N1 disposition;
- D_validation is used to repair the design.

### CALIBRATION_FAIL — valid negative result
If v24 executes exactly as frozen but either the 24-h or 48-h B-test result fails the Clopper-Pearson criterion, label the result `CALIBRATION_FAIL`.

This is a scientifically valid negative result, not a protocol-integrity failure. Reviewer A remains OPEN.

Neither state may be repaired adaptively on the same cohort.

## 22. Pre-freeze disposition

The statistical design is now substantially specified:

- primary N1 generator: joint full-day weather-profile derangement;
- 48-h dependence sensitivity: joint 48-h profile derangement;
- A -> B prospective time ordering;
- A1/A2 nested empirical multiplicity calibration;
- fixed 12-cell family with ineligible cells retained as p=1;
- fixed sham counts, seeds and proposal cap;
- explicit conditional-pass criterion;
- natural-driver RF results sealed until N1 disposition;
- D_validation excluded.

The score S = T/sqrt(D) is retained as a fixed support-standardized directional statistic. Because each cell receives its own empirical A1 null distribution before family-wise adjustment, no common parametric null scale across cells is assumed.

The 2500 A1 and 2500 A2 schedules give empirical p-value resolution 1/2501. The 5000 B-test schedules are used only for conditional Monte Carlo evaluation, not physical sample-size claims.

The frozen four-driver × three-horizon family defines the **bounded scope** of v24. It does not validate unrestricted future hypothesis discovery.

A defensible N2 natural negative control is **not required to execute N1**, but remains mandatory for a full natural-weather Reviewer-A PASS.

### Remaining steps before actual freeze

1. implement the v24 generator/calibration code exactly from this draft;
2. unit-test it on synthetic/toy data and historical development data only;
3. verify that no test or dry run can read D_validation;
4. create the machine-readable CALIBRATION_START manifest;
5. run one final adversarial code/protocol concordance audit;
6. only then create the freeze commit and start prospective accrual.

Current status:

**DRAFT — STATISTICAL DESIGN READY FOR IMPLEMENTATION — DO NOT EXECUTE ON PROSPECTIVE OUTCOMES — NO REVIEWER-A PASS CLAIMED.**
