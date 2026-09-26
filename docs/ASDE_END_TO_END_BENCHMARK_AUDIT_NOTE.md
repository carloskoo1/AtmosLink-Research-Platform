# ASDE End-to-End Benchmark Audit Note

The hidden-driver benchmark was developed through an explicit adaptive sequence on D_development.

- v17 constructed an initial candidate library from atmospheric transition events and introduced the pairwise overlap concept.
- v18 tested a 10-driver exploratory library against RF injections and exposed substantial distractor co-selection.
- v19 showed that, within a +/-60 minute event window, the 10-driver library formed a connected temporal co-occurrence graph and therefore did not support clean unique attribution.
- v20 evaluated atmospheric-only identifiability/support tradeoffs across event thresholds and refractory intervals. No RF recovery metric was used to rank the v20 candidate designs.
- The final 4-driver design uses the preregistered rule: at least 20 events per driver, pairwise +/-60 minute event overlap <=0.35, maximize independent-set size, then minimum and median event support. This selected the 85th-percentile / 360-minute-refractory design.

The resulting v21 audit is therefore confirmatory with respect to **new reserved simulation seeds and a frozen finite hypothesis library**, but it is not validation on an independent physical dataset. It quantifies reproducibility of hidden-driver recovery under the frozen benchmark design on the same real D_development background.

D_validation remains unopened and is not used for benchmark design, simulation calibration, or audit execution.

The maximum frozen pairwise overlap is 0.3478, close to the 0.35 admissibility limit. This must be reported rather than described as wide temporal separation.
