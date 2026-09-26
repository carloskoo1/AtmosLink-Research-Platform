# IEEE ASDE Literature Search Log

## Status
Scoping search in progress. This is not yet a PRISMA-style systematic review and must not be described as exhaustive.

## Cutoff
2026-09-26.

## Search axes
1. AI-assisted / autonomous scientific discovery and hypothesis validation.
2. Adaptive data analysis, holdout protection, multiple testing and falsification.
3. Environmental sensing and prediction using microwave/wireless link measurements.
4. Physics/domain-informed AI and controlled ablation.

## Representative sources reviewed

### Scientific discovery / hypothesis validation
- Huang K. et al. **Automated Hypothesis Validation with Agentic Sequential Falsifications.** ICML 2025, PMLR 267. POPPER uses agentic falsification and sequential testing with Type-I error control. Consequence for ASDE: falsification and automated hypothesis validation are not novel by themselves.
- Kulkarni A. et al. **Scientific Hypothesis Generation and Validation: Methods, Datasets, and Future Directions.** arXiv:2505.04651, 2025. Survey of LLM-driven generation/validation, simulation, causal modeling and human-AI collaboration.
- Wei J. et al. **From AI for Science to Agentic Science: A Survey on Autonomous Scientific Discovery.** arXiv:2508.14111, 2025. Broad agentic-science taxonomy.
- **Accelerating scientific discovery with Co-Scientist.** 2026. Multi-agent hypothesis generation and refinement with experimental validation as the intended downstream process.

### Statistical validity / adaptive analysis
- Dwork C. et al. **The reusable holdout: Preserving validity in adaptive data analysis.** Science 349(6248), 2015. DOI: 10.1126/science.aaa9375. Establishes the risk of adaptive reuse of holdout data.
- Benjamini Y., Hochberg Y. **Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing.** JRSS B 57(1), 1995. DOI: 10.1111/j.2517-6161.1995.tb02031.x.

### Domain-informed representation / ablation
- Yazdani-Jahromi M., Khodabandeh Yalabadi A., Ozmen Garibay O. **Equi-mRNA: Protein Translation Equivariant Encoding for mRNA Language Models.** arXiv:2508.15103, 2025. Encodes domain structure as inductive bias and uses controlled ablation with a common backbone. Relevant as methodological inspiration, not as a directly competing application.

### Wireless/environmental analytics
- **Detection of Precipitation Based on the Received Signal Level of Commercial Microwave Links and GRU Neural Networks.** IcETRAN 2024. DOI: 10.1109/IcETRAN62308.2024.10645130. Predefined precipitation-detection task from microwave-link measurements.
- **Model-based vs. Data-driven Approaches for Predicting Rain-induced Attenuation in Commercial Microwave Links: A Comparative Empirical Study.** IEEE conference paper, 2023. Predefined attenuation forecasting/prediction task.
- **Weather Attenuation Dataset Generation Method for Prediction-based Control of Non-Terrestrial High-Frequency Wireless Networks.** IEEE APWCS 2025. DOI: 10.1109/APWCS67981.2025.11151891. Focuses realistic weather-attenuation dataset generation and prediction-based control.
- **Weather Estimation for Integrated Sensing and Communication.** EuCNC/6G Summit 2026. DOI: 10.1109/EuCNC/6GSummit68295.2026.11577636. Multi-week experimental weather classification/regression using radio measurements.
- **Interpretable Microwave Sensing Using E-Band Commercial Links: Physics-Aware Deep Learning for Rainfall Detection.** Photonics 2026. Physics-aware predefined rainfall sensing on commercial-link data.
- David N. et al.-line literature on commercial microwave links for humidity/rain sensing demonstrates that RF-environment relationships are an established field; ASDE must not claim novelty for using RF telemetry as an environmental signal.

## Preliminary gap statement
The literature reviewed so far contains strong work on (a) agentic hypothesis generation/validation, (b) statistical validity under adaptivity and multiplicity, and (c) wireless links as environmental sensors or prediction sources. The candidate gap is their integration into an auditable open-ended discovery workflow for long-duration operational environmental–RF telemetry with QC-gated features, temporal event independence, pattern ontology, adaptive-analysis accounting, frozen provenance and a protected real holdout.

## Search still required before submission
- IEEE Xplore query combining: (scientific discovery OR hypothesis generation OR agentic) AND (wireless OR radio OR microwave OR RSSI OR SNR).
- Scopus/Web of Science query with the same conceptual blocks.
- Citation chasing from POPPER, Co-Scientist and the 2025 hypothesis-generation survey.
- Search for selective inference / post-selection inference specifically for autocorrelated time series.
- Search for RF anomaly-discovery frameworks that use synthetic ground-truth injection and explicit family-wise false-positive benchmarking.

No 'first' claim is authorized until these searches are completed and documented.

### Selective inference / data snooping additions
- Kuchibhotla A.K., Kolassa J.E., Kuffner T.A. **Post-Selection Inference.** Annual Review of Statistics and Its Application 9, 2022. DOI: 10.1146/annurev-statistics-100421-044639. Reviews sample splitting, simultaneous inference and conditional selective inference after exploration/model selection.
- Romano J.P., Wolf M. **Stepwise Multiple Testing as Formalized Data Snooping.** Econometrica 73, 2005. DOI: 10.1111/j.1468-0262.2005.00615.x. Relevant because a scientific-discovery engine is itself a data-snooping mechanism unless its hypothesis universe and multiplicity are controlled.
- Dependence-aware resampling literature (block bootstrap and resampling-based multiple testing) is relevant for future ASDE versions because atmospheric/RF time series violate row-wise independence. Current ASDE mitigates this operationally through event spacing and blocked evaluation but should not imply that this is a universal substitute for formal dependence-aware inference.

### Reliability and benchmark-risk additions
- **ControlA: Agentic Workflow Control Mechanisms for Reliable Science.** IEEE eScience 2025, DOI: 10.1109/eScience65000.2025.00086. Proposes agent- and workflow-level safeguards plus provenance instrumentation for reliable agentic science. Consequence for ASDE: provenance/safeguards are not novel by themselves; ASDE must differentiate through implemented statistical gates, autocorrelated RF telemetry, measurable false-positive behavior and candidate attrition.
- Luo Z., Kasirzadeh A., Shah N.B. **The More You Automate, the Less You See: Hidden Pitfalls of AI Scientist Systems.** arXiv:2509.08713, 2025. Identifies benchmark selection, data leakage, metric misuse and post-hoc selection bias, and argues that workflow traces/code are more revealing than final papers. Consequence: ASDE's ledger, freeze commits and full negative-result provenance are scientifically relevant evidence, not merely software hygiene.
- Lu C. et al. **Towards end-to-end automation of AI research.** Nature 651 (2026). Demonstrates end-to-end automated ideation, experimentation, writing and review. Consequence: ASDE must not claim novelty from end-to-end AI research automation; its role is deliberately narrower and validity-constrained.
- Ghareeb A.E. et al. **A multi-agent system for automating scientific discovery.** Nature 655 (2026). Robin couples literature search, hypothesis generation and data analysis agents with iterative experimental cycles. Consequence: hypothesis-generation/data-analysis loops are established prior art.

### Time-series benchmark additions
- Wu R., Keogh E. **Current Time Series Anomaly Detection Benchmarks are Flawed and are Creating the Illusion of Progress.** IEEE TKDE 35(3), 2023; DOI: 10.1109/TKDE.2021.3112126. Consequence: ASDE should emphasize benchmark design validity, full-grid reporting and morphology stress rather than headline recovery alone.
- Carmona C.U. et al. **Neural Contextual Anomaly Detection for Time Series.** arXiv:2107.07702, 2021. Uses synthetic anomaly injection to learn anomaly boundaries. Consequence: synthetic injection is established methodology and is not itself an ASDE novelty.
- Lavin A., Ahmad S. **Evaluating Real-Time Anomaly Detection Algorithms — The Numenta Anomaly Benchmark.** ICMLA 2015. Establishes controlled benchmarking of streaming anomaly detectors on real time-series backgrounds. Consequence: ASDE's novelty must lie in scientific-hypothesis screening and provenance constraints, not in benchmarking anomalies on time series.

### Targeted cross-domain search — 2026-09-26
Queries were run specifically for the intersection of scientific-discovery agents with wireless/RF time series, including combinations of `scientific discovery`, `hypothesis generation`, `agentic`, `wireless`, `radio`, `RSSI`, `SNR`, and `time series`.

Observed result families:
- general LLM/agentic scientific-discovery surveys and curated bibliographies;
- automated hypothesis-generation and validation frameworks;
- scientific-equation discovery agents;
- wireless resource-management agents using RSSI;
- supervised or digital-twin radio anomaly detection;
- Earth-science agentic-discovery roadmaps.

No directly matching primary work was identified in this targeted web search that simultaneously reports all of the following: open/bounded scientific hypothesis search over operational environmental–RF telemetry, explicit adaptive-analysis accounting, temporal-direction falsification for autocorrelated events, scientific-state ontology, analytically protected holdout, and auditable provenance with quantitative false-positive/recovery benchmarks.

**Interpretation limit:** this is negative search evidence only. It is not proof of absence and does not authorize a `first` claim. IEEE Xplore/Scopus/Web of Science structured searches and backward/forward citation chasing remain required before submission.

Additional adjacent sources surfaced:
- `Towards agentic science for advancing scientific discovery`, Nature Machine Intelligence 2025, DOI 10.1038/s42256-025-01110-x — broad responsible-agentic-science framing.
- `AI-Generated Hypotheses and the Emergence of Autonomous Scientific Discovery`, ACS Materials Letters 2026 — hypothesis-driven autonomous discovery perspective.
- `Anomaly detection using machine learning and adopted digital twin concepts in radio environments`, Scientific Reports 2025, DOI 10.1038/s41598-025-02759-5 — radio anomaly detection with simulated data and RSSI/SNR features, but not scientific-hypothesis workflow validation.
- `Automated Scientific Discovery: From Equation Discovery to Autonomous Discovery Systems`, arXiv:2305.02251 — broad automated-discovery survey and autonomy framing.
