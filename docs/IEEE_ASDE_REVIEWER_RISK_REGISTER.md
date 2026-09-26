# IEEE ASDE Reviewer Risk Register

## Purpose
Every major claim is paired with the strongest plausible reviewer objection. A claim is not upgraded until its corresponding risk is mitigated or explicitly disclosed.

| Risk | Likely reviewer objection | Current assessment | Required response |
|---|---|---|---|
| R1 Benchmark alignment | The injected joint RF degradation matches the composite RF detector and inflates recovery | **Real** | Keep v12 as primary frozen benchmark, but report v15 out-of-family morphology stress and explicitly limit the sensitivity claim |
| R2 AI role ambiguity | The statistically rigorous parts are deterministic; where exactly is the AI contribution? | **High** | Define an explicit AI interface: evidence packet -> candidate description/hypothesis proposal; prohibit AI from computing/altering statistics or promotion gates; benchmark the screening engine separately from language generation |
| R3 Synthetic ≠ natural discovery | Synthetic recovery does not prove that natural weather causes RF degradation | **Critical** | State this repeatedly. Synthetic benchmark validates machinery only. Natural causal claims require frozen D_validation and external replication |
| R4 Single-link generalization | Results may be specific to one 12-km high-altitude link | **High** | Frame as method validation plus case study; future cross-link replication is a limitation, not a hidden assumption |
| R5 Adaptive development | v1–v15 may overfit the 2860-row development dataset | **Controlled but important** | Preserve adaptive-analysis ledger; never call internal folds independent confirmation; D_validation stays unopened |
| R6 Temporal dependence | Rows/events are autocorrelated and p-values may be anti-conservative | **Partly controlled** | Use event-level refractory spacing, contiguous folds, pre/post tests, same-clock controls; quantify effective independent event counts |
| R7 Multiple testing | Many features/lags/horizons create selective reporting risk | **Controlled for primary benchmark** | Bonferroni family-wise correction for benchmark; FDR where exploratory families are broader; publish full grids, not only successful cells |

| Risk | Likely reviewer objection | Current assessment | Required response |
|---|---|---|---|
| R8 Sensor artifacts | Weather sensor faults can create apparent physical transitions | **Demonstrated** | Show PRESS_JUMP example and QC eligibility rule; report excluded features and counts |
| R9 Outcome construction | RF quality index averages heterogeneous RSSI/SNR/MCS variables | **Open** | Add sensitivity analysis to alternative outcome definitions: analog-only, DL-only, UL-only and/or standardized principal component; avoid asserting a unique physical degradation metric |
| R10 Event definition | 85th-percentile atmospheric driver and 180-min spacing were tuned during development | **Known** | Primary audit benchmark is valid only because protocol was frozen before audit seeds; do not present those choices as universally optimal |
| R11 Negative natural results | No natural precursor reached HYPOTHESIS/FROZEN status | **Not a defect** | Present candidate attrition as falsification case study; avoid marketing language implying a natural discovery occurred |
| R12 Context marker interpretation | CTX-0001 may be post-event consequence or shared regime, not physical driver | **Controlled by ontology** | Keep label INTERNAL_CONTEXT_MARKER; no prediction/causality claim |
| R13 Weak morphology sensitivity | MCS-only/gradual/partial degradations are detected less reliably | **Confirmed by v15** | Report recovery matrix; state operating envelope of current gate; motivate future multi-detector ensemble |
| R14 Reproducibility | Git history alone may not be enough to reproduce exact environment/data | **Open** | Add environment lock/requirements, immutable data manifest/hashes, one-command reproduction script, README and later DOI artifact |
| R15 Novelty over POPPER/agentic science | Falsification + AI hypothesis validation already exists | **High** | Novelty must be domain/process specific: operational wireless time series, QC gating, temporal ontology, adaptive ledger, real holdout and field platform; conduct documented systematic search |
| R16 Reviewer sees 'AI' as branding | LLM contribution may appear incidental to statistical pipeline | **High** | Either rigorously define and evaluate the AI-assisted candidate layer or reduce title emphasis on AI. Do not overbrand |

## Current publication gate
The manuscript may progress to a full draft when R1, R2, R9, R14 and R15 have concrete evidence/documents. Opening D_validation is **not** required to draft the Methods paper and must not be used merely to strengthen the narrative.

| R17 Screening benchmark vs discovery benchmark | v12 knows the atmospheric driver in advance and therefore validates screening more directly than open-ended discovery | **Critical, now being addressed** | Add end-to-end hidden-driver benchmark over a nonredundant candidate library; report exact-driver recovery, top-1 recovery and distractor co-selection |
| R18 Hypothesis-library redundancy | Different formulas can generate substantially overlapping event sets and inflate apparent discovery counts | **Confirmed** | Audit event-set overlap; collapse/reject highly redundant drivers before multiple testing; v17 retains 10 of 14 candidate drivers under <=0.35 overlap |
