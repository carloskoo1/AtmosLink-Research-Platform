# IEEE ASDE Comparator Matrix — Scoping Version

## Interpretation rule
This matrix records what is explicitly reported in the primary or authoritative source reviewed as of 2026-09-26. A blank or "not identified in reviewed source" entry is not a claim that the capability can never exist elsewhere in the system. This is a scoping comparison, not yet an exhaustive systematic review.

| Work | Main scientific function explicitly reported | Statistical / reliability mechanism explicitly reported | Provenance / workflow-control emphasis | Physical / operational data setting | Relevance to ASDE positioning |
|---|---|---|---|---|---|
| The AI Scientist (Lu et al., 2024) | Generates research ideas, writes code, executes ML experiments, visualizes results, writes papers, runs simulated review | Automated reviewer; no ASDE-like temporal screening claim identified in reviewed abstract | End-to-end automation is central; detailed statistical provenance is not the principal contribution in reviewed source | Machine-learning research domains | Rules out novelty claims based on end-to-end AI research automation |
| The AI Scientist-v2 (Yamada et al., 2025) | Iterative hypothesis formation, experiment execution, data analysis, visualization and manuscript generation via agentic tree search | Experiment-manager/tree-search workflow; no RF/time-series inferential gate identified in reviewed source | End-to-end autonomous workflow | ML research domains | Rules out novelty claims based on agentic iterative hypothesis/experiment loops |
| Co-Scientist (Gottweis et al., Nature 2026) | Multi-agent generation, critique, ranking and refinement of hypotheses; biomedical hypotheses experimentally evaluated | Tournament evolution and test-time compute scaling; downstream experimental verification | Multi-agent hypothesis evolution | Biomedical scientific problems with laboratory validation | Rules out novelty based on multi-agent hypothesis generation/refinement |
| Robin (Ghareeb et al., Nature 2026) | Literature search, hypothesis generation, experimental strategy, data analysis, interpretation and hypothesis update | Iterative experimental/data-analysis loop | Continuous multi-agent discovery workflow | Experimental biology | Rules out novelty based on iterative hypothesis–data-analysis cycles |
| POPPER (Huang et al., ICML 2025) | Automated validation of free-form hypotheses through agent-designed falsification experiments | Sequential testing with explicit Type-I error control | Falsification-oriented agent workflow | Six domains including biology, economics and sociology | Closest comparator to ASDE's falsification philosophy; ASDE cannot claim agentic falsification as novel |
| ControlA (Gueroudji et al., IEEE eScience 2025) | Reliability architecture for agentic scientific workflows | Agent-level safeguards and workflow-level instrumentation | Strong provenance-augmented infrastructure emphasis | General scientific workflows | Closest comparator to ASDE's audit/provenance framing; provenance and safeguards alone are not novel |
| PROV-AGENT (Souza et al., IEEE eScience 2025) | Captures agent prompts, responses, decisions and downstream workflow context | Reliability analysis supported through end-to-end provenance queries | Provenance is the primary contribution; extends W3C PROV for agent-centric metadata | General scientific workflows across edge/cloud/HPC | Rules out novelty claims based on logging prompts/responses/decisions or end-to-end agent provenance |
| HypoChainer (Jiang et al., IEEE TVCG 2026) | Human–LLM–knowledge-graph hypothesis construction and validation selection | KG-supported evidence and expert-guided prioritization rather than ASDE-style time-series directional gates | Interactive visual/human-in-the-loop reasoning trail | Biology-oriented scientific discovery | Rules out novelty from human–AI collaborative hypothesis construction and validation prioritization |
| Lin et al. (AI4Research 2025) | LLM-generated hypotheses from scientific literature with meta-analytic statistical evidence | Statistical evidence synthesis / meta-analysis | Evidence-grounded hypothesis generation | Literature-based scientific evidence synthesis | Rules out novelty from pairing LLM hypothesis generation with statistical rigor |
| Zhao et al. (IEEE Communications Magazine 2026) | Self-evolving multi-agent AI for wireless network/antenna optimization | Systematic validation inside autonomous optimization lifecycle | Supervisor-coordinated multi-agent cycle | Wireless networks / antenna optimization | Rules out novelty from applying agentic AI to wireless systems |
| THREAD-Bio (Ang et al., Biology 2026) | Trustworthy agentic bioinformatics with decision rights, validation gates, abstention and claim-to-evidence traceability | Separates execution, design, inference, biological and external validation; emphasizes pseudoreplication and calibrated claims | Strong claim-to-evidence and human-approval architecture | Bioinformatics / omics workflows | Rules out novelty claims based on validation gates, claim-to-evidence traceability, abstention or human approval as general concepts |
| Sargsyan (arXiv 2025) | Structural enforcement of statistical rigor in AI-driven discovery | Online FDR, sequential statistical state, declarative scaffolding, exploration/validation separation | Statistical protocol encoded into workflow architecture | Automated research / AI-scientist systems | Rules out novelty claims based on structurally enforced multiple-testing control or physically protected validation as general architecture |
| Plato-Bio (arXiv 2026) | Verification-first biological novelty screening | Frozen historical rediscovery and structural benchmarks; hypotheses retained as unvalidated | Explicit workflow states, provenance, citation checks and publication gates | Biology | Rules out novelty from verification-first states/publication gates alone |
| XScientist (arXiv 2026) | Git-like protocol for long-running autonomous scientific discovery | Quality gates and reproducibility artifacts | Exploration DAG, failed branches, content hashes and claim-to-evidence anchors | General autonomous research | Rules out novelty from Git-like scientific provenance, failed-branch retention or artifact-centered research protocols |
| LEDGER (arXiv 2026) | Claim-to-evidence trace graphs for auditing LLM agents | Audit coverage rather than ASDE-specific temporal inference | Evidence nodes, workflow nodes and typed claim-support edges | Long-horizon agent workflows | Rules out novelty from claim-to-evidence graphing itself |
| Reusable Holdout (Dwork et al., Science 2015) | Valid inference under repeated adaptive data analysis | Formal mechanisms for safe adaptive holdout reuse | Not an agentic workflow paper | General statistical data analysis | Establishes that adaptive data reuse threatens validity; ASDE's contribution can only be its operationalization in RF discovery |
| Post-Selection Inference review (Kuchibhotla et al., 2022) | Inference after exploration/model or variable selection | Sample splitting, simultaneous inference, conditional selective inference | Not a provenance workflow | General statistics | Rules out novelty claims based on sample splitting/post-selection awareness |
| Luo et al. (2025), hidden pitfalls of AI Scientist systems | Audits failure modes in AI scientist systems | Controlled experiments expose benchmark selection, leakage, metric misuse and post-hoc selection bias | Argues workflow traces/code are needed for reliable evaluation | AI scientist systems | Strong support for ASDE's trace-first audit philosophy, but also strong prior art on reliability concerns |
| Wu & Keogh (IEEE TKDE 2023) | Critiques time-series anomaly-detection benchmark validity | Shows benchmark design can create an illusion of progress | Not agentic | Time-series anomaly detection | Rules out novelty from benchmark skepticism itself; motivates ASDE's benchmark-audit discipline |
| Moharam et al. (Scientific Reports 2025) | ML anomaly detection in a digital-twin radio environment using features including RSSI/SNR | Supervised classification benchmark on simulated radio data | Digital-twin monitoring rather than scientific hypothesis provenance | Simulated radio environment | Demonstrates that wireless anomaly detection with RSSI/SNR is established prior art |
| Equi-mRNA (Yazdani-Jahromi et al., 2025) | Domain-structured equivariant representation for mRNA language models | Controlled comparison against vanilla baselines and task-level evaluation | Reproducible inductive-bias evaluation | Computational biology | Methodological inspiration: domain structure + controlled ablation; not a direct competitor |

## What ASDE should **not** claim
- first AI scientist;
- first autonomous or multi-agent hypothesis generator;
- first agentic falsification system;
- first provenance-aware agentic-science framework;
- first scientific validation-gate or claim-to-evidence architecture;
- first structurally enforced multiple-testing / protected-validation architecture for AI-driven discovery;
- first Git-like scientific provenance or publication-gate protocol;
- first agent-centric logging of prompts, responses, or decisions;
- first human–LLM collaborative hypothesis-construction workflow;
- first combination of LLM hypothesis generation with statistical evidence;
- first application of agentic AI to wireless systems;
- first use of holdout protection or multiple-testing correction;
- first anomaly detector for RSSI/SNR or wireless telemetry;
- first use of synthetic anomaly injection on time-series data;
- first domain-informed or physics-informed AI method.

## Narrow candidate novelty
The strongest current claim is not a new primitive algorithm or a new generic agentic-science architecture. It is an **implemented and quantitatively evaluated domain instantiation** for scientific inference from long-duration operational environmental–RF time series:

1. adaptive-analysis accounting that explicitly converts repeatedly inspected subsets into development data;
2. QC eligibility rules that can prevent sensor artifacts from entering the hypothesis space;
3. event-level temporal independence and blocked evaluation for autocorrelated telemetry;
4. explicit pattern ontology separating precursor, context marker, consequence/recovery and screened-out candidate;
5. strict pre/post falsification and multiplicity-controlled promotion gates;
6. bounded AI role: candidate formulation, mechanism alternatives, confounder elicitation and criticism, without authority to alter statistics or promote state;
7. hypothesis freezing plus analytically isolated real holdout;
8. hash-bound Git/data/protocol provenance and reconstructed audit metrics;
9. quantitative known-driver and hidden-driver benchmarks on the **real RF/weather background** of a field 6 GHz link;
10. explicit publication of negative candidate attrition and out-of-family failure modes.

## Claim language currently authorized
> ASDE is a falsification-oriented, provenance-aware workflow for bounded scientific discovery in autocorrelated environmental–radio telemetry. Its contribution is the operational integration and quantitative evaluation of adaptive-analysis accounting, QC-aware hypothesis eligibility, temporal-direction screening, multiplicity control, scientific pattern states, constrained AI assistance, and protected validation on a real field-measurement background.

The words "first", "novel" and "unique" are not authorized in the final manuscript until the remaining structured searches and citation-chasing are complete.
