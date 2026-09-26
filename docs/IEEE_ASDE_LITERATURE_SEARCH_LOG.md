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
