# IEEE ASDE Novelty Matrix — Working Review

## Rule
Novelty is not claimed from a single keyword search. The statements below are provisional and must be updated through a documented literature search before submission.

## Closest methodological lines

| Literature line | What it already does | What ASDE must not claim as novel | Candidate ASDE distinction |
|---|---|---|---|
| Adaptive data analysis / reusable holdout (Dwork et al., Science 2015) | Shows that repeated adaptive analysis can overfit a holdout and develops mechanisms for preserving validity | The general idea that adaptive reuse threatens statistical validity | Explicitly recognizing inspected wireless time blocks as development data, preserving a temporal RF holdout that is analytically isolated from candidate selection and tuning, and logging that transition in the scientific agent state |
| Multiple testing / FDR (Benjamini & Hochberg, 1995) | Controls false discoveries across many hypothesis tests | Multiple-testing correction itself | Embedding multiplicity control as one gate in a provenance-aware candidate state machine for serial wireless measurements |
| POPPER (Huang et al., ICML 2025) | Agentic sequential falsification of free-form hypotheses with Type-I error control | AI agents that falsify hypotheses; falsification as a principle | Domain-specific operationalization for autocorrelated RF/environmental telemetry: QC eligibility, temporal blocks, pre/post directionality, context-marker ontology, holdout embargo, and event-level evidence budgets |
| AI scientific-hypothesis surveys / agentic science (2025–2026) | Hypothesis generation, tool use, multi-agent refinement, validation workflows | General AI-for-science or agentic-science framing | A deliberately constrained agent where statistical code, QC and holdout rules dominate the LLM; the LLM proposes/interprets but cannot promote a candidate by itself |
| Equi-mRNA (Yazdani-Jahromi et al., arXiv:2508.15103) | Encodes domain structure as inductive bias; controlled ablations; fixed backbone; fuzzy relaxation | Domain-informed inductive bias or ablation as general ideas | Translating domain structure into RF-specific invariance/eligibility rules and testing which safeguards alter error behavior rather than merely predictive accuracy |

## Closest wireless/environmental lines

| Literature line | Typical objective | Gap relevant to ASDE |
|---|---|---|
| Commercial microwave-link precipitation detection (e.g., IEEE IcETRAN 2024 GRU study) | Predict or classify precipitation from received signal level | Prediction/sensing rather than auditable progression from exploratory association to scientific hypothesis |
| Rain-attenuation prediction and weather-aware wireless control | Forecast attenuation/network state | Usually assumes a target and optimizes predictive performance; does not address adaptive scientific hypothesis search over many environmental/RF variables |
| Physics-aware E-band rainfall sensing (2026) | Improve interpretable rainfall detection using physical constraints | Strong domain modeling, but task is predefined rainfall sensing rather than open-ended pattern discovery with holdout protection |
| 6G/ISAC weather estimation (EuCNC 2026) | Classify/regress weather from radio measurements | Treats RF as a sensor with labeled outcomes, not as a scientific-discovery process over long operational telemetry |

## Provisional novelty statement
A defensible working claim is:

> ASDE is an auditable, falsification-oriented scientific-discovery workflow for long-duration environmental–radio telemetry that couples AI-assisted candidate generation to QC-aware feature eligibility, blocked temporal evaluation, strict temporal-direction tests, multiplicity control, pattern ontology, adaptive-analysis accounting, immutable provenance, and an untouched confirmatory holdout.

Do **not** claim that ASDE is the first AI scientist, the first automated hypothesis validator, the first wireless anomaly detector, or the first use of weather/RF data.

## Evidence required before final novelty claim
1. Documented searches in IEEE Xplore, Scopus/Web of Science or equivalent, arXiv and Google Scholar.
2. Search strings and cutoff date recorded.
3. At least three literature clusters covered: AI scientific discovery, adaptive/statistical inference, and environmental/wireless measurement analytics.
4. A comparison table of the 10–20 closest methods using fixed criteria rather than narrative similarity.
5. Any paper that combines agentic hypothesis generation with wireless time-series validation must be examined in full before claiming novelty.
