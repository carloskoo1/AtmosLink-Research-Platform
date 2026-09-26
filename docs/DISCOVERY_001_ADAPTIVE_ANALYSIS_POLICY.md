# DISCOVERY-001 Adaptive Analysis Policy

## Rationale

Versions v1-v5 repeatedly used both the original discovery block and the original characterization block to choose representations, thresholds, clustering structures, screening rules and candidate families.

Therefore, from v5 onward, the former D_characterization block must no longer be described as an independent replication set for newly generated candidates. Repeated adaptive inspection has converted it into development data.

## Revised roles

- D_development = original D_discovery + original D_characterization = 2860 complete-core observations.
- D_validation = 716 observations, unchanged and still embargoed.
- External configuration cohorts remain unavailable for confirmatory claims until a hypothesis is frozen.

The change is prospective and methodological. It does not alter or delete previous provenance; it prevents future overstatement of independence.

## Development evaluation

Future pattern development must use blocked temporal resampling inside D_development rather than random row splits.

Four contiguous reference folds are registered:

1. 2026-09-01 18:30:52 UTC to 2026-09-04 08:02:17 UTC.
2. 2026-09-04 08:12:19 UTC to 2026-09-07 05:14:26 UTC.
3. 2026-09-07 05:19:27 UTC to 2026-09-09 18:41:57 UTC.
4. 2026-09-09 18:46:58 UTC to 2026-09-13 03:29:49 UTC.

Algorithms may be developed and stress-tested across these folds, but success in these folds is internal robustness, not external confirmation.

## Validation access rule

D_validation may be opened only after:
- a candidate definition is frozen;
- features, thresholds, lag/horizon and outcome definition are frozen;
- all QC exclusions are frozen;
- the statistical test and multiplicity rule are frozen;
- the expected decision rule is registered;
- human scientific review approves the validation run.

No tuning is allowed after validation results are observed.
