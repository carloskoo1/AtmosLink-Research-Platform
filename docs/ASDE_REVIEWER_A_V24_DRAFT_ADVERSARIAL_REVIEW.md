# Reviewer A — adversarial review of v24 calibration draft

**Status:** PRE-FREEZE REVIEW.  
**Target:** `ASDE_REVIEWER_A_V24_PROSPECTIVE_CALIBRATION_PROTOCOL_DRAFT.md`.  
**Disposition:** **NOT READY TO FREEZE** until the Major items below are resolved.

## A1. Symmetric cross-fitting weakens prospective time ordering — Major

The draft proposes A->B and B->A as co-primary and pools them. This is statistically useful cross-validation but weakens the clean prospective interpretation because the later Fold B would be used to calibrate decisions on earlier Fold A.

**Required correction:** make A->B primary:
- first 30 eligible days = calibration fold;
- next 30 eligible days = held-out evaluation fold;
- no RF inferential result is inspected until both folds are accrued.

B->A may be reported only as a secondary transport/symmetry diagnostic.

## A2. Raw max of S may be dominated by cell-specific null scale — Major

The proposed score S=(post-only-pre-only)/sqrt(D) partially normalizes support but does not guarantee comparable null distributions across the 12 driver-horizon cells. Background hardness already demonstrated driver-specific behavior.

**Required correction:** derive a cellwise empirical tail probability from calibration sham schedules, then perform family-wise calibration on the minimum cellwise empirical p (or an equivalent calibrated max transform). Do not assume S has the same null scale across cells.

The procedure must use disjoint calibration and evaluation sham seeds.

## A3. Sham eligibility is underspecified — Major

Matching local hour and RF observability is insufficient. A sham anchor can accidentally overlap a true frozen-driver atmospheric event or an operational incident, contaminating the intended no-exposure schedule.

**Required correction:** a sham anchor must:
- be >=120 min from every frozen-driver atmospheric event;
- be outside maintenance/outage/configuration-transition exclusion windows;
- satisfy the paired RF observation geometry;
- satisfy the same edge constraints as a real anchor;
- respect >=360-min spacing from every other sham anchor in the schedule.

If the exact driver-specific count/hour histogram cannot be constructed under these constraints, the schedule is infeasible. Do not drop events, merge hours or relax spacing after inspection.

## A4. Sham-replicate uncertainty is not physical uncertainty — Major

Five thousand sham schedules can make the Monte Carlo interval arbitrarily narrow on one RF background. That does not create 5000 independent field episodes.

**Required correction:** report two uncertainty layers separately:
1. conditional Monte Carlo uncertainty across sham schedules;
2. physical-background sensitivity using the held-out calendar-day structure and the prespecified 48-h analysis.

No effective physical sample size may be replaced by sham-draw count.

## A5. Sixty days is a volume gate, not an independence certificate — Major but already partly addressed

The draft correctly says 60 days are not 60 independent episodes. Retain that language. Remove any later wording that implies a zero-selection binomial bound over 60 days unless day-level independence is demonstrated.

## A6. Primary support threshold remains inherited, not validated — Minor/Major boundary

D>=8 was inherited from v23 and did not alter v23 selection beyond multiplicity. It can be retained as a fixed minimum-information eligibility rule, but the manuscript must not call it an empirically demonstrated safeguard.

## A7. One-hour strata may be infeasible — Major if unresolved before freeze

Exact one-hour matching is scientifically desirable for diurnal control but may be combinatorially infeasible under spacing/exclusion constraints.

**Required pre-freeze feasibility check:** use weather/QC/metadata only on D_development to estimate schedule-construction feasibility. RF outcomes must not be used. This is a design-feasibility diagnostic, not evidence for v24 performance.

If one-hour matching is frequently infeasible, choose the final stratum width before CALIBRATION_START_UTC and document why. Do not switch after prospective RF outcomes are available.

## A8. N1 and N2 must remain separate — Critical claim boundary

Randomized sham schedules provide a design-based algorithmic null. They do not establish natural-weather exchangeability.

**Required wording:** Reviewer A may grant only a conditional N1 calibration pass from v24 sham results. A full natural-weather PASS requires prespecified N2 negative controls or external physical replication.

## A9. Actual natural-driver results should not contaminate the calibration study — Major

The v24 primary analysis should estimate calibration using sham schedules. Applying the learned threshold to actual natural driver events is a distinct scientific question.

**Required correction:** do not inspect or report held-out natural-driver RF selection until the N1 calibration analysis is finalized and immutable. If natural-driver testing is desired, preregister it as a separate phase.

## Pre-freeze verdict

The v24 direction is substantially better than another post-hoc sensitivity on D_development. However, the draft is **NOT READY TO FREEZE** until A1–A4, A7 and A9 are incorporated and a weather-only one-hour matching feasibility diagnostic is completed.

No D_validation use is authorized.


## Resolution update after pre-freeze feasibility work

### A1 — resolved in draft
Primary temporal direction is now strictly Fold A -> Fold B. Fold A is the first 30 eligible local days and calibrates; Fold B is the next 30 and evaluates. Reverse B -> A can only be secondary.

### A2 — resolved in draft
The primary family-wise procedure no longer compares raw S values across cells. Fold A is split into A1 cellwise empirical calibration and A2 joint family-wise calibration. Held-out B scores receive cellwise empirical tails from A1 and a family-wise adjustment from the A2 distribution of the minimum cellwise p.

### A3 — revised after symmetry critique
The original review proposed conditioning sham construction on RF observation availability and excluding nearby real weather events. That would make sham existence depend on properties that do not determine whether real atmospheric events occur.

The revised N1 design therefore constructs sham schedules from weather/time/operational metadata only. RF availability is applied **after schedule construction** through the same matched-offset observation rule used for real events. N1 also does not require a weather-free neighborhood; overlap with real weather is reported as background structure. Natural no-exposure controls belong to N2.

### A4 — partly resolved
The draft now states that sham draws are conditional Monte Carlo replicates and never independent field episodes. Physical dependence is reported at local-day level with a 48-h prespecified sensitivity. A numeric Conditional-N1 acceptance rule is still unresolved.

### A7 — resolved for stratum width, generator still open
An exact binary-MILP feasibility diagnostic used D_development weather/time only, with no RF columns and no D_validation.

Under exact event-count matching and >=360-min sham spacing:

| Design | CU temp rise | SJ temp fall | SJ RH fall | SJ pressure rise |
|---|---:|---:|---:|---:|
| 1-h, exclude all driver neighborhoods | no | no | no | no |
| 1-h, exclude same-driver neighborhoods | no | no | no | no |
| 1-h, no weather exclusion | yes | yes | **no** | yes |
| 2-h, exclude all driver neighborhoods | no | no | no | no |
| 2-h, exclude same-driver neighborhoods | no | yes | no | no |
| 2-h, no weather exclusion | **yes** | **yes** | **yes** | **yes** |

Therefore 12 two-hour strata are now primary for N1. One-hour matching remains a secondary sensitivity and is never allowed to replace the primary result.

Artifact: `Results/scientific_discovery/DISCOVERY-001/reviewer_a_v24_sham_feasibility_exact.json`.  
Runner: `scripts/check_asde_v24_sham_feasibility_exact.py`.

This diagnostic establishes constructive feasibility only. It does **not** define the probability distribution from which thousands of sham schedules will be sampled.

### A9 — resolved in draft
Natural-driver RF scores in Fold B remain sealed until N1 calibration is completed and immutable. Any natural-driver analysis requires a separate preregistration.

## Remaining pre-freeze Major items

### V24-M1 — sham generator distribution not yet frozen
MILP proves that valid 2-h schedules exist; it does not define a reproducible stochastic generator. The final protocol must specify:
- candidate-anchor universe;
- ordering rule;
- random choice mechanism;
- restart/rejection rule;
- maximum attempts;
- behavior when a schedule is infeasible;
- A1/A2/B seed families.

Changing the generator after CALIBRATION_START_UTC is prohibited.

### V24-M2 — Conditional N1 acceptance rule not numerically defined
The draft specifies the endpoint but not the exact criterion for declaring it acceptably calibrated. This must be fixed before freeze. The criterion must not treat 5000 shams as 5000 physical episodes.

### V24-M3 — 24-h vs 48-h contradiction rule undefined
The current phrase "material contradiction" is not operational. The freeze must state exactly which discrepancy changes the Reviewer-A disposition.

### V24-M4 — support handling must preserve the 12-cell family
If a cell is ineligible because D<8 or too few support days, it must remain in the registered family with a null/nonselectable state; the family size cannot shrink opportunistically schedule by schedule.

## Current pre-freeze verdict

**IMPROVED, BUT NOT READY TO FREEZE.**

A1, A2, A3, A7 and A9 are addressed. V24-M1 through V24-M4 remain mandatory before a CALIBRATION_START_UTC can be created.


## Final pre-implementation resolution

A further weather/time-only feasibility study tested **joint multivariate day-profile derangement**. On seven complete D_development local days, 20,000 uniformly proposed full derangements were evaluated; 3,190 preserved the >=360-min same-driver refractory constraint, for an acceptance fraction of 0.1595. No RF columns or D_validation were read.

This supersedes individual-anchor matching as the primary N1 generator because it preserves exact local times and within-day cross-driver event structure while randomizing alignment with the RF day sequence.

The v24 draft now additionally fixes:

- full-day joint-profile derangement as primary N1 generator;
- joint 48-h profile derangement as dependence sensitivity;
- A1/A2/B-test seed families and accepted-schedule counts;
- 1,000,000 proposal cap per seed family;
- p=1 for support-ineligible cells so the test family remains exactly 12 cells;
- one-sided 95% Clopper-Pearson conditional calibration criterion;
- with 5000 B-test schedules, at most 224 selections can satisfy the upper-bound <=0.05 criterion;
- NOT_CALIBRATED versus CALIBRATION_FAIL as distinct dispositions.

### Pre-implementation verdict

**STATISTICAL DESIGN READY FOR IMPLEMENTATION, NOT READY FOR PROSPECTIVE FREEZE.**

The remaining work is code concordance, unit testing, source isolation and creation of the future CALIBRATION_START manifest. No prospective RF outcome may be inspected during that work.
