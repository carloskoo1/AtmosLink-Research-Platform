# IEEE ASDE Reviewer Risk Register

## Purpose
Every major claim is paired with the strongest plausible reviewer objection. A claim is not upgraded until its corresponding risk is mitigated or explicitly disclosed.

| Risk | Likely reviewer objection | Current assessment | Required response |
|---|---|---|---|
| R1 Benchmark alignment | The injected joint RF degradation matches the composite RF detector and inflates recovery | **Real** | Keep v12 as primary frozen benchmark, but report v15 out-of-family morphology stress and explicitly limit the sensitivity claim |
| R2 AI role ambiguity | The statistically rigorous parts are deterministic; where exactly is the AI contribution? | **Safety constrained; incremental utility pending blind review** | The AI Role Contract, frozen pilot protocol, deterministic B0 baseline, prospectively frozen A1 inputs, and automated A1 safety audit are implemented. A1 produced zero numeric/state/holdout violations across six candidates. Two blinded human reviewers must still determine whether A1 adds scientific utility beyond B0. |
| R3 Synthetic ≠ natural discovery | Synthetic recovery does not prove that natural weather causes RF degradation | **Critical** | State this repeatedly. Synthetic benchmark validates machinery only. Natural causal claims require frozen D_validation and external replication |
| R4 Single-link generalization | Results may be specific to one 12-km high-altitude link | **High** | Frame as method validation plus case study; future cross-link replication is a limitation, not a hidden assumption |
| R5 Adaptive development | v1–v15 may overfit the 2860-row development dataset | **Controlled but important** | Preserve adaptive-analysis ledger; never call internal folds independent confirmation; D_validation remains analytically embargoed |
| R6 Temporal dependence | Rows/events are autocorrelated and p-values may be anti-conservative | **Partly controlled** | Use event-level refractory spacing, contiguous folds, pre/post tests, same-clock controls; quantify effective independent event counts |
| R7 Multiple testing | Many features/lags/horizons create selective reporting risk | **Controlled for primary benchmark** | Bonferroni family-wise correction for benchmark; FDR where exploratory families are broader; publish full grids, not only successful cells |

| Risk | Likely reviewer objection | Current assessment | Required response |
|---|---|---|---|
| R8 Sensor artifacts | Weather sensor faults can create apparent physical transitions | **Demonstrated** | Show PRESS_JUMP example and QC eligibility rule; report excluded features and counts |
| R9 Outcome construction | RF quality index averages heterogeneous RSSI/SNR/MCS variables | **Characterized, not resolved** | v16 shows CTX-0001 is outcome-definition-sensitive: present under all6/analog/UL-oriented definitions but absent under DL-only. Report this sensitivity and avoid asserting a unique physical degradation metric. |
| R10 Event definition | 85th-percentile atmospheric driver and 180-min spacing were tuned during development | **Known** | Primary audit benchmark is valid only because protocol was frozen before audit seeds; do not present those choices as universally optimal |
| R11 Negative natural results | No natural precursor reached HYPOTHESIS/FROZEN status | **Not a defect** | Present candidate attrition as falsification case study; avoid marketing language implying a natural discovery occurred |
| R12 Context marker interpretation | CTX-0001 may be post-event consequence or shared regime, not physical driver | **Controlled by ontology** | Keep label INTERNAL_CONTEXT_MARKER; no prediction/causality claim |
| R13 Weak morphology sensitivity | MCS-only/gradual/partial degradations are detected less reliably | **Confirmed by v15** | Report recovery matrix; state operating envelope of current gate; motivate future multi-detector ensemble |
| R14 Reproducibility | Git history alone may not be enough to reproduce exact environment/data | **Substantially mitigated; DOI pending** | Environment/package pins, artifact SHA-256 manifest, v21 reconstruction verifier, holdout-isolation audit and one-command publication verification are implemented. A DOI-bearing immutable release is still required before submission. |
| R15 Novelty over POPPER/agentic science | Falsification + AI hypothesis validation already exists | **Provisionally narrowed; structured database search pending** | Comparator matrix now explicitly covers AI Scientist/v2, Co-Scientist, Robin, POPPER, ControlA, adaptive holdout/post-selection, TSAD benchmark criticism, radio anomaly detection and Equi-mRNA. Candidate novelty is the implemented composition for autocorrelated environmental–RF telemetry, not any individual primitive. No 'first' claim is authorized until IEEE Xplore/Scopus/Web of Science searches and citation chasing are complete. |
| R16 Reviewer sees 'AI' as branding | LLM contribution may appear incidental to statistical pipeline | **Decision rule frozen; human utility result pending** | Keep 'AI-Assisted' in the title only if the blinded pilot satisfies the preregistered title-retention rule. Otherwise use the non-AI title and describe the LLM as an optional constrained interface. |

## Current publication gate
**Full-draft ready:** yes. The method, known-driver audit, hidden-driver audit, failure-mode stress tests, reproducibility record and claim ledger are sufficient to draft the complete Methods manuscript without opening D_validation.

**Submission-ready:** not yet. Before submission, the following remain mandatory:
- complete the blinded two-reviewer AI utility pilot and apply the frozen title rule;
- complete structured IEEE Xplore/Scopus/Web of Science searches plus citation chasing for the final novelty statement;
- create a DOI-bearing immutable code/data artifact permitted for release;
- run a final adversarial manuscript review against this risk register and claim ledger.

Opening D_validation is **not** required for the Methods paper and must not be used merely to strengthen the narrative.

| R17 Screening benchmark vs discovery benchmark | v12 knows the atmospheric driver in advance and therefore validates screening more directly than discovery | **Mitigated within a bounded hypothesis library** | v21 freezes a 4-driver library and hides the planted truth. Report exact-driver selection, unique top-1 ranking, distractor co-selection and null FWER. Do not generalize this to unrestricted/open-ended hypothesis discovery. |
| R18 Hypothesis-library redundancy | Different formulas can generate substantially overlapping event sets and inflate apparent discovery counts | **Mitigated for v21 finite library** | v19 rejected the 10-driver library as a connected temporal co-occurrence graph at +/-60 min. v20 selected a frozen 4-driver maximum independent set under <=0.35 overlap, minimum 20-event support, and 360-min refractory spacing. Maximum frozen overlap is 0.3478 and must be disclosed. |

### R13 follow-up: exploratory multiview detector
A post-audit multiview detector (global/RSSI/SNR/MCS views with Bonferroni correction over 12 view-horizon tests) was evaluated as an attempted remedy for morphology sensitivity. It did not uniformly solve the problem: at 1.0 SD, MCS-only recovery was 0.46/0.45/0.30 for 15/30/60-minute lags; RSSI-only was 0.68/0.95/0.00; SNR-only was 1.00/1.00/0.00. Its empirical null detection rate was 0.024 over 500 shifts. Therefore multiview is retained as exploratory evidence and is **not** adopted as the primary detector or presented as a solved robustness problem.
