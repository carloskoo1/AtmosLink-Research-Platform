# IEEE ASDE Manuscript Outline

## Target
IEEE Access — Methods manuscript (primary option). The paper focuses on a new auditable scientific-discovery workflow and its quantitative validation. The natural-link analysis is a case study, not the primary causal claim.

## Working title
**ASDE: An Auditable AI-Assisted Scientific Discovery Engine for Atmospheric–Radioelectric Pattern Screening in a Rural High-Altitude 6 GHz Link**

## Alternative shorter title
**Auditable AI-Assisted Scientific Discovery for Long-Duration 6 GHz Wireless Measurements**

## Draft abstract
Long-duration wireless measurement campaigns create an attractive setting for AI-assisted scientific discovery, but serial dependence, multiple testing, adaptive overfitting, sensor artifacts, and post hoc hypothesis formation can transform exploratory associations into false scientific claims. This paper presents the AtmosLink Scientific Discovery Engine (ASDE), an auditable human-in-the-loop workflow for discovering and screening atmospheric–radioelectric patterns in operational wireless-link measurements. ASDE separates exploratory candidate generation from data-quality eligibility, temporal blocking, pre/post directionality, multiplicity control, context-marker classification, hypothesis freezing, and independent holdout validation. The framework is evaluated on the real background of a rural high-altitude 6 GHz link. In the natural development data, six apparently promising atmospheric–RF candidates were rejected before validation, while one persistent association was retained only as a context marker because temporal precedence was not established. To quantify discovery performance under known ground truth without opening the real holdout, a benchmark protocol was frozen in Git before an audit-grade synthetic injection experiment. Across 100 trials per effect-lag condition and 1000 circular-shift null trials, the full ASDE gate achieved a family-wise false-positive rate of 2.5% (95% CI: 1.70–3.66%). For injected effects of 1.0 robust standard deviation, recovery was 100%, 100%, and 94% at lags of 15, 30, and 60 min, respectively. An ablation showed that an uncorrected screening rule increased the false-positive rate to 7.9%. These results demonstrate that AI-assisted discovery can be coupled to explicit statistical and provenance safeguards that prioritize falsification and reproducibility over candidate generation.

## Index terms
AI-assisted scientific discovery; wireless measurements; 6 GHz; high-altitude radio links; reproducibility; multiple testing; time-series analysis; environmental sensing; human-in-the-loop AI; experimental methodology.

## Main contributions
1. **Auditable discovery architecture.** A stateful workflow that distinguishes candidate generation, context association, hypothesis formation, freezing, and validation.
2. **Adaptive-analysis protection.** Explicit recognition that repeatedly inspected data become development data; a separate 716-observation real holdout remains unopened.
3. **Temporal-causality safeguards.** Pseudoreplication control, pre/post directionality tests, blocked temporal robustness, and separation of precursors from persistent context markers.
4. **QC-aware feature eligibility.** Sensor-quality events can disqualify derived features from discovery, preventing instrumental artifacts from becoming scientific candidates.
5. **Ground-truth benchmark on real background data.** Frozen synthetic injections quantify family-wise false positives and recovery across effect sizes and lags.
6. **Ablation of safeguards.** The naive uncorrected rule produces 7.9% false positives versus 2.5% for the full ASDE gate on the audit-grade benchmark, while moderate-signal recovery remains high.

## Key quantitative results
- Frozen benchmark protocol commit: 1e49129.
- Audit-grade result commit: 975bcf7.
- Null trials: 1000.
- Family-wise ASDE false-positive rate: 0.025; Wilson 95% CI [0.0170, 0.0366].
- Naive uncorrected false-positive rate: 0.079.
- 1.0-SD recovery: 1.00 at 15 min, 1.00 at 30 min, 0.94 at 60 min.
- 0.5-SD recovery: 1.00 at 15 min, 0.84 at 30 min, 0.62 at 60 min.
- Natural-data candidate attrition: 6 RFATM candidates screened out before validation; 1 internal context marker retained; 0 frozen natural hypotheses.
- Real D_validation: 716 observations, still embargoed.

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
- 716-row untouched D_validation.
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
F. CTX-0001 as a context marker, not a precursor.

### VIII. Discussion
- ASDE is designed to reject attractive but unsupported patterns.
- Why candidate rejection is a positive methodological outcome.
- Identifiability depends on event spacing and lag.
- Difference between validating the discovery machinery and validating a natural causal effect.

### IX. Limitations
- Single physical link and geographic environment.
- Synthetic benchmark validates detection behavior but cannot prove natural causal mechanisms.
- Natural holdout has not yet been opened because no natural hypothesis has met the freeze gate.
- Current benchmark uses a specific family of injected degradations and should later be expanded to additional signal morphologies.
- External cross-link replication remains future work.

### X. Conclusion
ASDE demonstrates a reproducible way to integrate AI-assisted candidate generation with falsification-oriented statistical safeguards in operational wireless research.

## IEEE submission notes
- Primary manuscript type: Methods.
- Keep main paper below approximately 20 pages where practical; move exhaustive simulation grids to supplementary material.
- Provide source code and machine-readable benchmark results as supplemental/repository material.
- Include the required disclosure of AI-generated text/code assistance in the acknowledgments, identifying the AI system and the parts of the work for which it was used.
- Authors retain responsibility for all scientific claims, analyses, code, and final manuscript content.
