# IEEE ASDE Manuscript Outline

## Target
IEEE Access — Methods manuscript (primary option). The paper focuses on a new auditable scientific-discovery workflow and its quantitative validation. The natural-link analysis is a case study, not the primary causal claim.

## Conditional title policy
**Title A — only if the blinded AI-contribution pilot passes the preregistered title-retention rule:**  
**ASDE: An Auditable AI-Assisted Scientific Discovery Workflow for Long-Duration Environmental–Radio Telemetry**

**Title B — default if incremental AI utility is not demonstrated:**  
**ASDE: An Auditable Scientific Discovery Workflow for Long-Duration Environmental–Radio Telemetry**

The title decision is intentionally deferred until blinded human scoring is complete. The statistical method, benchmarks and natural-data case study do not depend on that outcome.

## Draft abstract
Long-duration wireless measurement campaigns create opportunities for AI-assisted scientific discovery, but serial dependence, multiple testing, sensor artifacts, adaptive data reuse, and post hoc hypothesis formation can convert exploratory associations into unreliable scientific claims. This paper presents the AtmosLink Scientific Discovery Engine (ASDE), an auditable human-in-the-loop workflow for atmospheric–radioelectric pattern discovery in operational wireless telemetry. The AI component is restricted to candidate formulation, mechanistic alternatives, confounder identification, and structured criticism; numerical evidence, multiplicity control, candidate promotion, and validation gates are executed by deterministic versioned procedures. ASDE combines quality-control-based feature eligibility, temporally blocked development analysis, event-level independence, pre/post directionality, multiplicity correction, pattern ontology, immutable provenance, hypothesis freezing, and an analytically isolated real-data holdout. The framework is evaluated on the background of a rural high-altitude 6 GHz link. In natural development data, six apparently promising atmospheric–RF candidates were screened out, and one additional association remained only an outcome-definition-sensitive context signal. A frozen known-driver benchmark first evaluated the screening gate, yielding a family-wise false-positive rate of 2.5% and 94–100% recovery for 1.0 robust-SD joint RF effects at 15–60 min lags. More importantly, a post-freeze hidden-driver benchmark required ASDE to recover the planted atmospheric driver from four competing prespecified hypotheses. Its library-wide null false-positive rate was 2.0% (95% CI: 1.30–3.07%). For 1.0 robust-SD effects, exact-driver selection was 85.3%, 79.0%, and 21.3% at 15, 30, and 60 min, while unique top-1 ranking was 94.5%, 89.5%, and 59.5%, respectively. These results quantify both the operating envelope and the conservatism of the workflow: ASDE can often identify the most plausible candidate while refusing promotion when evidence is insufficient. The study validates a bounded discovery-and-screening process, not a natural atmospheric causal effect.

## Index terms
AI-assisted scientific discovery; wireless measurements; 6 GHz; high-altitude radio links; reproducibility; multiple testing; time-series analysis; environmental sensing; human-in-the-loop AI; experimental methodology.

## Main contributions
1. **Auditable discovery architecture.** A stateful workflow that distinguishes candidate generation, context association, hypothesis formation, freezing, and validation.
2. **Adaptive-analysis protection.** Explicit recognition that repeatedly inspected data become development data; a separate 716-observation real holdout remains analytically isolated from candidate selection, tuning, screening, and benchmark development.
3. **Temporal-causality safeguards.** Pseudoreplication control, pre/post directionality tests, blocked temporal robustness, and separation of precursors from persistent context markers.
4. **QC-aware feature eligibility.** Sensor-quality events can disqualify derived features from discovery, preventing instrumental artifacts from becoming scientific candidates.
5. **Two-level ground-truth evaluation on real background data.** A frozen known-driver benchmark isolates screening-gate behavior, while a separately frozen hidden-driver benchmark tests exact recovery from a finite prespecified hypothesis library.
6. **Quantified conservatism and failure modes.** Safeguard ablation, morphology stress tests, outcome-definition sensitivity, per-driver recovery, and post-audit background-hardness diagnostics explicitly map where ASDE succeeds and where it loses sensitivity.

## Key quantitative results
- Known-driver screening protocol commit: 1e49129; audit result commit: 975bcf7.
- Known-driver screening null trials: 1000; family-wise FPR = 0.025, Wilson 95% CI [0.0170, 0.0366].
- Known-driver 1.0-SD recovery = 1.00, 1.00, 0.94 at 15/30/60 min; naive uncorrected FPR = 0.079.
- Hidden-driver frozen benchmark commit: 63839e8; 4-driver x 3-horizon hypothesis family; 1000 library-wide null trials.
- Hidden-driver library-wide null FWER = 0.020, Wilson 95% CI [0.0130, 0.0307].
- Hidden-driver 1.0-SD exact selection = 0.8525, 0.7900, 0.2125 at 15/30/60 min.
- Hidden-driver 1.0-SD unique top-1 ranking = 0.9450, 0.8950, 0.5950 at 15/30/60 min.
- Aggregate distractor co-selection = 0 in the audited injected cells; per-cell 0/400 upper Wilson bound is approximately 0.0095.
- Natural-data candidate attrition: 6 RFATM candidates screened out before validation; 1 exploratory outcome-definition-sensitive context association retained; 0 frozen natural hypotheses.
- Real D_validation: 716 observations, still embargoed from scientific analysis and candidate evaluation.

## Section plan

### I. Introduction
- Scientific opportunity: long-duration operational links produce multivariate time series suitable for AI-assisted discovery.
- Scientific risk: autocorrelation, data dredging, adaptive overfitting, instrumental anomalies, and post hoc hypotheses.
- Gap: most AI/data-analysis pipelines optimize prediction or anomaly detection rather than auditable progression from candidate to scientific hypothesis.
- Contributions listed explicitly.

### II. Related Work
A. Environmental effects in microwave/6 GHz terrestrial links.  
B. AI/ML for wireless monitoring and anomaly detection.  
C. Automated or AI-assisted scientific discovery.  
D. Reproducibility, holdout protection, and selective inference in time series.  
E. Positioning of ASDE relative to prediction-oriented methods.

### III. AtmosLink Experimental Platform
- 12 km high-altitude link and sites.
- 6 GHz radio telemetry.
- CU01/SJ01 local meteorology.
- ERA5-Land/NASA POWER as external contextual sources where applicable.
- Synchronization, QC and provenance.

### IV. ASDE Architecture
- Observation layer.
- QC eligibility layer.
- Structured representation.
- Candidate generation.
- Screening gates.
- Pattern ontology: precursor, context marker, consequence/recovery, screened-out.
- Human review and freeze.
- Independent validation.

### V. Adaptive Analysis and Holdout Protection
- Original discovery/characterization split.
- Why repeated inspection converted characterization into development data.
- Four contiguous development folds.
- 716-row D_validation protected from scientific analysis and adaptive candidate evaluation.
- No random-row cross-validation for serial data.

### VI. Synthetic Ground-Truth Benchmark
- Real background preserved.
- Frozen driver definition and event spacing.
- Fixed RF-drop detector threshold.
- Injection grid, lags, effect sizes and activation probability.
- Null circular shifts.
- Bonferroni family-wise correction.
- Audit-grade seeds and Git checkpoint.

### VII. Results
A. False-positive control.  
B. Recovery as a function of effect size and lag.  
C. Horizon sensitivity.  
D. Safeguard ablation.  
E. Natural-data candidate attrition.  
F. CTX-0001 outcome-definition sensitivity: why it cannot be promoted to a robust context marker or precursor.

### VIII. Discussion
- ASDE is designed to reject attractive but unsupported patterns.
- Why candidate rejection is a positive methodological outcome.
- Identifiability depends on event spacing and lag.
- Difference between validating the discovery machinery and validating a natural causal effect.

### IX. Limitations
- Single physical link and geographic environment.
- Synthetic benchmark validates detection behavior but cannot prove natural causal mechanisms.
- Natural holdout has not yet been used for scientific analysis because no natural hypothesis has met the freeze gate.
- The preregistered benchmark uses joint abrupt RF degradations. A post-audit morphology stress test shows lower sensitivity for DL/UL-only, MCS-only, and gradual effects; therefore benchmark performance must not be generalized to arbitrary degradation morphology.
- External cross-link replication remains future work.

### X. Conclusion
ASDE demonstrates a reproducible way to integrate AI-assisted candidate generation with falsification-oriented statistical safeguards in operational wireless research.

## IEEE submission notes
- Primary manuscript type: Methods.
- Keep main paper below approximately 20 pages where practical; move exhaustive simulation grids to supplementary material.
- Provide source code and machine-readable benchmark results as supplemental/repository material.
- Include the required disclosure of AI-generated text/code assistance in the acknowledgments, identifying the AI system and the parts of the work for which it was used.
- Authors retain responsibility for all scientific claims, analyses, code, and final manuscript content.

## End-to-end hidden-driver audit (v21)
A second frozen benchmark evaluates discovery rather than screening alone. The candidate library contains four prespecified atmospheric drivers selected using atmospheric-only identifiability criteria before audit execution. For each trial, one driver is hidden as the synthetic truth and ASDE must select it from the competing library under Bonferroni correction across 4 drivers x 3 horizons.

Audit commit: `63839e8`.

Primary end-to-end results:
- library-wide circular-shift null FWER: **0.020**, Wilson 95% CI **[0.0130, 0.0307]**;
- 1.0 robust-SD exact-driver selection: **0.8525** at 15 min, **0.7900** at 30 min, **0.2125** at 60 min;
- 1.0 robust-SD unique top-1 ranking: **0.9450**, **0.8950**, **0.5950** at 15/30/60 min;
- no distractor co-selection was observed in any aggregate injected cell; the 95% upper Wilson bound is approximately 0.0095 for 0/400 trials per cell.

The large difference between ranking accuracy and gate-passing selection at 60 minutes is scientifically important: ASDE often identifies the most plausible driver but correctly refuses to promote it when evidence is insufficient under the frozen statistical gate.

## Background-hardness diagnostic (v22)
Post-audit analysis shows that the real RF background is not exchangeable across candidate drivers. For example, before synthetic injection, CU01 temperature-rise events show 10 post-only versus 2 pre-only RF entries within 30 min, whereas SJ01 pressure-rise events show 3 post-only versus 5 pre-only. Therefore end-to-end recovery is partly a property of both the method and the natural background surrounding each driver. Aggregate recovery must always be accompanied by per-driver results.
