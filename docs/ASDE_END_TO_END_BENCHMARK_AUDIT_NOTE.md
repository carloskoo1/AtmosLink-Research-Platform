# ASDE End-to-End Benchmark Audit Note

The hidden-driver benchmark was developed through an explicit adaptive sequence on D_development.

- v17 constructed an initial candidate library from atmospheric transition events and introduced the pairwise overlap concept.
- v18 tested a 10-driver exploratory library against RF injections and exposed substantial distractor co-selection.
- v19 showed that, within a +/-60 minute event window, the 10-driver library formed a connected temporal co-occurrence graph and therefore did not support clean unique attribution.
- v20 evaluated atmospheric-only identifiability/support tradeoffs across event thresholds and refractory intervals. No RF recovery metric was used to rank the v20 candidate designs.
- The final 4-driver design uses the preregistered rule: at least 20 events per driver, pairwise +/-60 minute event overlap <=0.35, maximize independent-set size, then minimum and median event support. This selected the 85th-percentile / 360-minute-refractory design.

The resulting v21 audit is therefore confirmatory with respect to **new reserved simulation seeds and a frozen finite hypothesis library**, but it is not validation on an independent physical dataset. It quantifies reproducibility of hidden-driver recovery under the frozen benchmark design on the same real D_development background.

D_validation remains embargoed from scientific analysis and is not used for benchmark design, simulation calibration, candidate evaluation, or audit execution.

The maximum frozen pairwise overlap is 0.3478, close to the 0.35 admissibility limit. This must be reported rather than described as wide temporal separation.

## Freeze supersession record
An initial freeze checkpoint (`4e75429`) was created before v21 execution. The immediate post-commit cleanliness check detected that three v15 exploratory result files had changed during the staging/commit interval. Inspection showed that the versioned v15 generator was newer than the staged v15 outputs. No v21 audit seed had been executed. The v15 outputs were regenerated from the committed generator and reproduced deterministically. A new freeze checkpoint supersedes `4e75429`; the original commit remains in history for auditability.

The regenerated v15 artifacts were rerun once more before the superseding freeze and reproduced byte-for-byte. SHA-256: morphology_recovery.csv = a449cf984c24e50c72dd993e43c221cbae98f1877f8fde15770cc2944562fe10; morphology_trials.csv = 920578b4f690ecd128165e2d7afe9fc2c884cefec44fa5195b8821b484ad39c3; v15_summary.json = 21d5d24f84e08500faf58c05342bffda23323f78a3dcc425470de7359c950381.

Immediately before the superseding freeze, `scripts/audit_discovery_holdout_isolation.py` checked the active v7-v21 development/audit scripts and returned PASS: no active script referenced the full integrated campaign CSV or the registered D_validation tokens/boundaries. This establishes analytical isolation of the active pipeline; it does not claim that source-file bytes were never historically read when the split was originally constructed.
