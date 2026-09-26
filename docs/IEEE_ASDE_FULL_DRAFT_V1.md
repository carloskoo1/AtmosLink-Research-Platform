# ASDE — IEEE Access Methods Manuscript — Full Draft v1

> Working draft. Not submission-ready. Title remains conditional on the blinded AI-contribution pilot.

## Conditional title
**AI-retained route:** ASDE: An Auditable AI-Assisted Scientific Discovery Workflow for Long-Duration Environmental–Radio Telemetry

**Default route:** ASDE: An Auditable Scientific Discovery Workflow for Long-Duration Environmental–Radio Telemetry

## Abstract
Long-duration wireless measurement campaigns create opportunities for scientific discovery, but serial dependence, multiple testing, sensor artifacts, adaptive data reuse, and post hoc hypothesis formation can convert exploratory associations into unreliable claims. This paper presents the AtmosLink Scientific Discovery Engine (ASDE), an auditable human-in-the-loop workflow for atmospheric–radioelectric pattern discovery in operational wireless telemetry. The optional language-model layer is restricted to candidate formulation, mechanistic alternatives, confounder identification, and structured criticism; numerical evidence, multiplicity control, candidate promotion, and validation gates are executed by deterministic versioned procedures. ASDE combines quality-control-based feature eligibility, temporally blocked development analysis, event-level independence, pre/post directionality, multiplicity correction, pattern ontology, hash-bound versioned provenance, hypothesis freezing, and an analytically isolated real-data holdout. The framework is evaluated on the background of a rural high-altitude 6 GHz link. In natural development data, six apparently promising atmospheric–RF candidates were screened out, and one additional association remained only an outcome-definition-sensitive context signal. A frozen known-driver benchmark first evaluated the screening gate, yielding an empirical family-wise false-positive rate of 2.5% and 94–100% recovery for the registered 1.0 robust-SD joint RF perturbation at 15–60 min lags. A separate post-freeze hidden-driver benchmark then required ASDE to recover the planted atmospheric driver from four competing prespecified hypotheses. Its library-wide null false-positive rate was 2.0% (95% CI: 1.30–3.07%). For 1.0 robust-SD effects, exact-driver selection was 85.3%, 79.0%, and 21.3% at 15, 30, and 60 min, while unique top-1 ranking was 94.5%, 89.5%, and 59.5%, respectively. These results quantify both the operating envelope and the conservatism of the workflow: a candidate may rank first yet remain unpromoted when evidence is insufficient. The study quantitatively evaluates a bounded discovery-and-screening process under frozen synthetic-ground-truth audits; it does not establish a natural atmospheric causal effect.

## Index Terms
scientific discovery; wireless measurements; 6 GHz; environmental sensing; reproducibility; multiple testing; time-series analysis; human-in-the-loop AI; hypothesis validation; experimental methodology.

# I. Introduction

Operational wireless links increasingly expose rich telemetry streams that include received signal strength, signal-to-noise ratio, modulation state, throughput, latency, retransmissions, availability, and, in instrumented deployments, colocated environmental measurements. Such data create an opportunity to move beyond predefined prediction tasks and ask a broader scientific question: can reproducible environmental–radio patterns be discovered from long-duration field observations without turning exploratory correlation into scientific overclaim?

This question is becoming more important as AI systems enter the scientific workflow. Systems such as The AI Scientist and The AI Scientist-v2 automate substantial parts of ideation, experimentation, analysis, and manuscript production, while Co-Scientist and Robin use multi-agent architectures to generate, critique, refine, and experimentally interrogate scientific hypotheses [AI-SCIENTIST-2024, AI-SCIENTIST-V2-2025, CO-SCIENTIST-2026, ROBIN-2026]. POPPER goes further toward formal validation by combining agentic falsification with sequential Type-I-error control [POPPER-2025]. These systems establish that hypothesis generation, critique, and even iterative experimental reasoning can be automated; therefore, those capabilities cannot by themselves constitute the novelty of a new scientific-discovery workflow.
At the same time, the statistical literature shows why unconstrained automation can be dangerous. Repeated adaptive analysis invalidates the naive assumption that a holdout remains independent after repeated inspection, and post-selection inference requires explicit treatment of exploration and selection [REUSABLE-HOLDOUT-2015, POST-SELECTION-2022]. Recent audits of AI scientist systems have identified benchmark selection, data leakage, metric misuse, and post-hoc selection bias as concrete failure modes, and have argued that workflow traces and code reveal failures that final manuscripts alone can conceal [AI-SCIENTIST-PITFALLS-2025]. In time-series research, benchmark design itself can create an illusion of progress, particularly when temporal dependence, event boundaries, and anomaly definitions are not carefully controlled [TSAD-BENCHMARKS-2023].

Wireless and radio research already contains extensive work on anomaly detection, propagation prediction, and using radio links as environmental sensors. Recent radio-environment anomaly frameworks use features such as RSSI and SNR, and commercial microwave-link research has long treated received signal measurements as informative about environmental state [RADIO-DT-2025]. These studies typically begin with a predefined target—such as anomaly class, precipitation, or attenuation—and optimize predictive performance. ASDE addresses a different methodological problem: how to manage an evolving scientific hypothesis space over autocorrelated operational telemetry while preserving explicit provenance, falsification gates, and a protected path to confirmation.

A second line of related work concerns reliability and provenance in agentic science. ControlA proposes agent- and workflow-level safeguards embedded in provenance-aware infrastructure [CONTROLA-2025]. This prior work means that provenance and workflow safeguards are also not novel primitives. ASDE therefore does not claim novelty for AI agents, falsification, holdouts, multiplicity correction, provenance, or synthetic injection individually. The candidate contribution is their domain-specific operational integration and quantitative evaluation for environmental–radio telemetry collected from a real field link.

The core design principle is simple: **candidate generation is not evidence, and ranking is not validation**. ASDE records exploratory candidates, subjects them to deterministic scientific gates, distinguishes precursors from context markers and consequences, freezes hypotheses before confirmatory use of protected data, and retains rejected candidates as part of the scientific record.

The contributions of this work are:
1. an auditable state-machine architecture for candidate generation, screening, hypothesis freezing, and validation;
2. explicit accounting for adaptive reuse of development data and analytical isolation of a real holdout;
3. temporal-independence and pre/post directionality gates tailored to serial environmental–RF telemetry;
4. QC-aware feature eligibility and a scientific pattern ontology that separates precursor, context, consequence/recovery, and screened-out states;
5. two synthetic-ground-truth evaluations on the real AtmosLink background: a known-driver screening audit and a finite hidden-driver discovery audit;
6. explicit failure-mode characterization through safeguard ablation, morphology stress, outcome-definition sensitivity, and driver-specific background-hardness analysis;
7. a constrained AI interface whose scientific value is evaluated separately from the deterministic statistical engine.

# II. Related Work

## A. AI-Assisted and Autonomous Scientific Discovery
The AI Scientist introduced an end-to-end framework that generates research ideas, implements experiments, analyzes results, and writes research papers in machine-learning domains [AI-SCIENTIST-2024]. The AI Scientist-v2 extended this approach using agentic tree search and a dedicated experiment manager [AI-SCIENTIST-V2-2025]. Co-Scientist uses specialized agents for hypothesis generation, reflection, ranking, and evolution, and has been evaluated in biomedical settings with downstream experimental validation [CO-SCIENTIST-2026]. Robin integrates literature search, hypothesis generation, experimental strategy, and analysis of laboratory results in an iterative multi-agent workflow [ROBIN-2026].

POPPER is especially relevant because it treats free-form hypothesis validation as an agentic falsification problem and couples agent-generated tests to sequential statistical control [POPPER-2025]. ControlA is similarly relevant from the reliability side: it proposes workflow instrumentation, agent-level safeguards, and provenance-aware control mechanisms for reliable scientific workflows [CONTROLA-2025]. These works narrow ASDE's defensible contribution. ASDE does not claim to invent agentic falsification or provenance-aware scientific workflows; rather, it operationalizes a bounded form of these ideas for autocorrelated environmental–RF telemetry with explicit temporal event semantics and field-measurement provenance.

## B. Adaptive Analysis, Post-Selection Inference, and Benchmark Validity
Scientific-discovery systems are intrinsically adaptive: each observed pattern can change the next query, model, threshold, or representation. The reusable-holdout literature formalized the general danger of repeated adaptive reuse of data, while post-selection inference provides a broader framework for inference after exploration or model selection [REUSABLE-HOLDOUT-2015, POST-SELECTION-2022]. ASDE incorporates this concern operationally. Once the originally designated characterization block had been repeatedly inspected during development, it was formally reclassified as development data rather than continuing to be described as independent replication.

This distinction also applies to benchmarks. Time-series anomaly-detection research has shown that benchmark construction can materially distort apparent progress [TSAD-BENCHMARKS-2023]. ASDE therefore separates exploratory benchmark development from post-freeze audit runs, records the protocol and randomization state before confirmatory simulation, and retains failed or superseded benchmark variants as provenance.

## C. Wireless/Environmental Analytics
Wireless anomaly detection and opportunistic environmental sensing already use radio-derived variables such as RSSI, SNR, received signal level, and attenuation. Recent digital-twin work evaluates machine-learning anomaly detection in simulated radio environments [RADIO-DT-2025]. Separately, microwave-link environmental sensing has a substantial prior literature: commercial communication links have been used to infer rainfall and other atmospheric information from signal attenuation and received-power measurements [MESSER-2006, LEIJNSE-2007, UIJLENHOET-2018]. Recent work has also examined the information contribution of environmental variables to commercial-microwave-link rainfall estimation [SPACKOVA-2025]. Therefore, ASDE does not claim novelty from the premise that atmospheric state and radio measurements can be statistically related.

The methodological distinction proposed in ASDE is narrower. Rather than beginning from a fixed target such as rainfall retrieval, anomaly class, or a prespecified propagation response, the workflow manages candidate relationships that emerge during adaptive analysis and subjects them to QC eligibility, event-level independence, temporal-direction tests, multiplicity control, provenance constraints, and hypothesis freezing before protected validation. This creates a different evaluation problem from conventional supervised prediction, fixed-target retrieval, or anomaly classification.

## D. Domain Structure and Controlled Ablation
Equi-mRNA provides a useful methodological analogy from a different domain: domain structure is encoded explicitly and evaluated through controlled comparison rather than left as implicit model behavior [EQUI-MRNA-2025]. ASDE applies a related principle at the workflow level. RF and atmospheric structure enters through event definitions, QC eligibility, time ordering, configuration metadata, and explicit scientific states. Ablations then quantify the cost and benefit of safeguards rather than treating the entire workflow as an opaque AI system.

# III. Experimental Platform and Data Governance

## A. AtmosLink Field Platform
AtmosLink is a rural high-altitude wireless research platform deployed in Cajamarca, Peru. The link connects CU01 at approximately 2,730 m above sea level and SJ01 at approximately 3,650 m above sea level over an approximately 12-km line-of-sight path. The 6 GHz experimental link uses Cambium ePMP 4600C equipment, with CU01 operating as the access-point/master side and SJ01 as the subscriber side.

Local meteorological sensing is available at both sites. The core DISCOVERY-001 variables include CU01 temperature, relative humidity, and pressure; SJ01 temperature, relative humidity, pressure, and wind speed; and RF variables comprising DL/UL RSSI, DL/UL SNR, and DL/UL MCS. External products such as ERA5-Land and NASA POWER are maintained by the broader AtmosLink platform for contextual and reconciliation tasks but are not required for the primary DISCOVERY-001 benchmark described here.

## B. Primary Cohort and Configuration
The primary DISCOVERY-001 cohort uses the 7000 MHz / 20 MHz configuration from the integrated 6 GHz campaign export. The registered source file contains 3,576 complete-core observations for this configuration and is identified by SHA-256 in the experiment manifest.

The original chronological partition was:
- discovery: 2,145 observations;
- characterization: 715 observations;
- validation: 716 observations.

No random row split was used. The validation block spans the final registered interval and is marked as embargoed for scientific discovery.

## C. Adaptive Reclassification of Development Data
During v1–v5, both the original discovery and characterization blocks were repeatedly inspected while choosing representations, thresholds, event definitions, clustering structures, and screening rules. Continued description of the characterization block as independent replication would therefore overstate its inferential status. ASDE formally reclassified the first 2,860 observations as D_development and reserved the final 716 observations as D_validation.

The development set is evaluated using four contiguous temporal folds of 715 observations each. These folds support robustness analysis but are not described as external confirmation. This policy explicitly treats repeated human/AI inspection as a source of adaptive overfitting.

The 716-observation D_validation block remains analytically isolated from candidate selection, tuning, screening, and benchmark development. ASDE does not claim that the underlying source-file bytes were never historically read when the partition was first constructed; the scientific claim is narrower and auditable: validation values have not been used as evidence in the active candidate-development pipeline.

Additional 6 GHz configuration cohorts are registered for future cross-configuration replication, including 6475/20 MHz, 6655/20 MHz, 7000/40 MHz, and 6655/40 MHz. They are not used as confirmatory evidence in the results reported here.

# IV. ASDE Architecture

## A. Scientific State Machine
ASDE uses an explicit state model rather than treating every high-scoring association as a result:

CANDIDATE -> SCREENED_OUT

or

CANDIDATE -> HUMAN_REVIEWED -> HYPOTHESIS -> FROZEN -> VALIDATING -> CONFIRMED | REJECTED | INCONCLUSIVE.

An intermediate EVIDENCE_ACCUMULATING state may be used during development when a pattern is directionally persistent but remains too uncertain for hypothesis promotion. Candidate identifiers are immutable, and screened-out candidates remain in the registry.

The state machine is intentionally asymmetric: promotion requires additional evidence, while falsification can occur at any registered screening gate. No language-model output can directly execute a promotion transition.

## B. QC-Aware Feature Eligibility
A scientific-discovery engine can easily mistake instrumentation artifacts for physical structure. ASDE therefore treats quality-control status as part of the hypothesis space itself. Features can remain eligible as contextual levels while their derivatives are quarantined from candidate generation if rapid changes are known to be unreliable.

A concrete example occurred for CU01 pressure. The prevalidation quality report contained repeated PRESS_JUMP warnings, including extreme short-term changes capable of dominating standardized derivatives. ASDE retained pressure level as contextual information but excluded its rapid derivative from transition discovery until signal eligibility could be restored. This is not a post hoc deletion of inconvenient data; it is a registered feature-eligibility rule tied to a documented sensor-quality condition.

## C. Temporal Event Representation
Repeated telemetry rows are not treated as independent scientific evidence. ASDE constructs event or episode representations with refractory intervals so that a persistent state cannot contribute dozens of nominally independent observations.

Atmospheric transitions are derived from short-window changes in meteorological variables, while RF response is represented through robust standardized combinations of DL/UL RSSI, SNR, and MCS. Depending on the experiment version, the engine studies absolute degradation state, transition into degradation, or sharp quality drop.

Temporal claims are directional. If an atmospheric event is proposed as a precursor, ASDE compares RF events before and after that event. Block-level enrichment alone is insufficient.

## D. Pattern Ontology
ASDE separates four scientific interpretations:

1. PRECURSOR_CANDIDATE — a temporally asymmetric pattern that occurs before an RF event, survives blocked robustness analysis, and is not equivalently present after the event;
2. CONTEXT_MARKER — a reproducible association present around RF events without evidence of temporal precedence;
3. CONSEQUENCE_OR_RECOVERY — a pattern primarily detectable after an RF event;
4. SCREENED_OUT — a candidate that fails a registered scientific gate.

This ontology prevents a common semantic error in exploratory analysis: labeling any association near an event as a precursor or cause.

## E. Constrained AI Layer
The language-model component is intentionally bounded. It receives machine-generated evidence packets rather than unrestricted raw telemetry whenever possible. It may describe candidate patterns, propose mechanistic alternatives, identify potential confounders, propose registered falsification tests, and recommend continued screening or human review.

It may not invent statistics, alter thresholds, change holdout boundaries, remove failed candidates, declare validation, or promote a candidate. Statistical evidence and state transitions are implemented by deterministic versioned code plus human scientific review.

Because this design makes the AI non-authoritative, the incremental value of the language-model layer is evaluated separately from the statistical engine through a frozen blinded pilot described later.

# V. Quantitative Evaluation Design

## A. Known-Driver Screening Audit
The first audit isolates the behavior of the statistical screening gate when the atmospheric driver is already defined. The driver is constructed from rapid SJ01 warming combined with relative-humidity decrease. Eligible local peaks are temporally separated to reduce event overlap. Synthetic RF degradations are then injected into a copy of the real development background; the original telemetry is never modified.

The registered perturbation family is a joint degradation of DL/UL RSSI, SNR, and MCS. Effect magnitudes are expressed in robust standard-deviation units derived from the unmodified RF background. Registered effect magnitudes are 0.5, 1.0, 1.5, and 2.0 robust SD; lags are 15, 30, and 60 min; duration is 15 min; and an eligible atmospheric event activates the synthetic RF perturbation probabilistically under the frozen simulation design.

The RF-drop detector is frozen from the unmodified development background before simulation. Candidate analysis horizons are 30, 60, and 120 min. Family-wise alpha is divided across these horizons. A trial is recovered only when the directional test is significant under the corrected threshold, sufficient discordant events are available, and the post-event direction is preserved in at least three of four contiguous development folds.

The empirical null is generated by circularly shifting the atmospheric driver timing relative to the unchanged RF background. The audit uses reserved simulation seeds after the protocol is frozen in Git. This benchmark answers a screening question; it does not measure open-ended discovery because the driver is known to the analysis.

## B. Hidden-Driver End-to-End Audit
A second benchmark was designed specifically to address the known-driver limitation. The search procedure is given a finite library of competing atmospheric drivers but is not told which driver generated the synthetic RF response.

The final library was selected using atmospheric data only. Candidate driver events are defined from short-window robust standardized changes with an event threshold and refractory interval frozen before the audit. Drivers must satisfy a minimum event-support requirement and a pairwise temporal-proximity constraint. Under the registered selection rule, the final library contains four drivers:
- CU01 temperature rise;
- SJ01 temperature fall;
- SJ01 relative-humidity fall;
- SJ01 pressure rise.

The final event counts are 23, 28, 28, and 28, respectively. Because inference is event-based rather than row-based, these counts are more relevant than the 2,860 development rows for understanding effective support. Their distribution across the four contiguous development folds is:

| Frozen driver | Total events | Fold 1 | Fold 2 | Fold 3 | Fold 4 |
|---|---:|---:|---:|---:|---:|
| CU01 temperature rise | 23 | 6 | 7 | 5 | 5 |
| SJ01 temperature fall | 28 | 8 | 7 | 6 | 7 |
| SJ01 relative-humidity fall | 28 | 8 | 8 | 5 | 7 |
| SJ01 pressure rise | 28 | 8 | 8 | 6 | 6 |

Thus, every frozen driver contributes events to every temporal fold, with 5–8 events per fold. This mitigates row-level pseudoreplication but does not imply complete statistical independence between atmospheric processes. The maximum pairwise event overlap within the registered temporal-proximity window is close to, but does not exceed, the admissibility threshold. This limitation is reported explicitly rather than described as wide separation.

For each simulation trial, exactly one candidate driver is designated as hidden truth. Joint RF degradation is injected after that driver's events using registered effect magnitudes, lags, duration, and activation probability. The search algorithm receives all four driver event sets plus the resulting RF event series, but not the planted identity.

Every driver is tested at three response horizons, producing a 4-by-3 family of directional tests. Bonferroni correction is applied over the full family. A driver is selected only if at least one horizon passes the corrected directional test, minimum discordant-event support, and temporal-fold direction requirement.

The primary endpoints are exact-driver selection, exclusive exact-driver selection, unique top-1 ranking, distractor co-selection, mean selected-driver count, and library-wide null family-wise error. Unique top-1 ranking is reported separately from statistical selection: ranking first does not promote a candidate.

The audit uses independent reserved simulation seeds after a clean Git freeze. A library-wide circular-shift null jointly shifts all four atmospheric event sets so that their cross-driver temporal structure is preserved relative to one another while their relation to the RF background is broken.

## C. Post-Audit Stress and Diagnostic Analyses
Several analyses are intentionally classified as exploratory because they were designed after observing the primary audits.

First, morphology stress testing changes the synthetic RF perturbation from the registered joint abrupt degradation to alternative forms, including gradual joint changes and perturbations affecting only a subset of RF metrics. These experiments characterize the detector's operating envelope but are not used to redefine the primary audit.

Second, a multi-view detector using global, RSSI, SNR, and MCS views was evaluated as a possible remedy for sparse-subsystem perturbations. Multiplicity was corrected across views and horizons. Because the extension did not uniformly improve recovery, it was not adopted as the primary detector.

Third, outcome-definition sensitivity evaluates how selected real-data associations depend on alternative RF degradation definitions. This analysis is exploratory because it was performed after candidate identification.

Finally, a post-audit background-hardness diagnostic measures natural pre/post RF-event asymmetry around each frozen hidden-driver event family. This diagnostic helps interpret heterogeneous recovery but does not retune the audit.

## D. AI Contribution Pilot
The scientific AI layer is evaluated separately from the statistical engine. Six already-screened-out natural candidates are used in a prospective pilot. A deterministic rule-based baseline and a constrained language-model output receive equivalent bounded candidate evidence. The AI output is forbidden from inventing numbers, claiming validation, accessing the holdout, changing failed-gate decisions, or proposing tests outside a registered vocabulary.

Hard safety endpoints are checked automatically. Incremental scientific utility is assessed by at least two blinded domain-competent human reviewers using frozen scoring dimensions for interpretive completeness, alternative-explanation usefulness, falsifiability, confounder coverage, and actionability. The final manuscript title retains the phrase AI-Assisted only if the preregistered utility rule is satisfied. At the time of this draft, the safety audit is complete and the blinded utility review remains pending.

# VI. Results

## A. Natural-Data Candidate Attrition
DISCOVERY-001 generated multiple apparently plausible atmospheric–RF relationships during adaptive development. None reached the frozen-hypothesis state.

| Candidate | Exploratory pattern | Final development decision |
|---|---|---|
| RFATM-0001 | SJ01 pressure level associated with later DL RSSI/SNR degradation | SCREENED_OUT: association did not preserve magnitude or sign across development periods |
| RFATM-0002 | CU01 humidity inversely associated with DL MCS | SCREENED_OUT: association was not stable after temporal trend/diurnal screening |
| RFATM-0003 | Cold–humid–calm regime associated with degraded RF state | SCREENED_OUT: block-level risk reversed under temporally independent replication |
| RFATM-0004 | Multivariate atmospheric transition followed by sharp RF-quality drop | SCREENED_OUT: RF drops were not more frequent after transitions than before them |
| RFATM-0005 | Lower SJ01 humidity variability before RF drops | SCREENED_OUT: failed multiplicity/replication and post-event negative-control requirements |
| RFATM-0006 | Rapid SJ01 warming/drying followed by apparent RF degradation enrichment | SCREENED_OUT: pre/post temporal direction was inconsistent |

This attrition is a central result of the methodology. Several candidates looked promising under weaker analyses, including block-level enrichment or row-level association, but were rejected when subjected to stronger temporal or multiplicity controls. D_validation was not used to rescue any failed candidate.

An additional humidity-variability association, CTX-0001, was retained only as an exploratory context signal. Later outcome-definition sensitivity showed that the association appeared under the all-metric, analog-oriented, and UL-oriented event definitions but not under a DL-only event definition. It is therefore not presented as a robust precursor or validated marker.

## B. Known-Driver Screening Audit
Under the frozen known-driver benchmark, the full ASDE screening gate produced an empirical family-wise false-positive rate of 0.025 across 1000 registered circular-shift null trials, with Wilson 95% CI [0.0170, 0.0366].

| Injected effect | Lag 15 min | Lag 30 min | Lag 60 min |
|---|---:|---:|---:|
| 0.5 robust SD | 1.00 | 0.84 | 0.62 |
| 1.0 robust SD | 1.00 | 1.00 | 0.94 |
| 1.5 robust SD | 1.00 | 1.00 | 0.97 |
| 2.0 robust SD | 1.00 | 1.00 | 0.97 |

Thus, within the registered joint RF perturbation family, recovery was high at short and intermediate lags and lower at the longest registered lag; this statement is restricted to the frozen perturbation family and benchmark design.

A safeguard ablation showed a lower empirical false-positive rate for the complete frozen gate than for a naive uncorrected rule on the same audit-grade trials: 0.025 versus 0.079. This comparison supports the combined gate within the registered benchmark; it does not identify the independent contribution or necessity of each safeguard.

## C. Morphology Stress Test
The strong known-driver result is not morphology-invariant. A post-audit exploratory stress test challenged the detector with perturbations outside the registered joint abrupt family.

At 1.0 robust SD per affected metric:

| Morphology | 15 min | 30 min | 60 min |
|---|---:|---:|---:|
| Joint abrupt 15-min step | 1.00 | 1.00 | 0.98 |
| Joint 30-min ramp | 1.00 | 1.00 | 0.77 |
| Joint sustained 60-min step | 1.00 | 1.00 | 0.98 |
| RSSI-only 15-min step | 0.74 | 0.50 | 0.08 |
| SNR-only 15-min step | 0.74 | 0.50 | 0.08 |
| MCS-only 15-min step | 0.74 | 0.50 | 0.08 |

The composite detector therefore has a clear operating envelope: it is highly sensitive to coherent multi-metric degradation but can dilute sparse subsystem-specific changes, especially at longer lags.

An exploratory multi-view extension attempted to address this weakness by testing global, RSSI, SNR, and MCS views under multiplicity correction across views and horizons. The empirical null detection rate remained low (0.024 over the registered exploratory null shifts), but recovery improved inconsistently: SNR-only perturbations improved at short lags, while some long-lag RSSI/SNR conditions collapsed and MCS-only recovery remained limited. The multi-view extension was therefore not adopted as the primary detector.

## D. Hidden-Driver End-to-End Audit
The hidden-driver audit is more demanding because the search procedure must choose among competing atmospheric hypotheses. Under 1000 joint circular-shift null trials, the four-driver library produced a family-wise false-positive rate of 0.020, with Wilson 95% CI [0.0130, 0.0307].

The primary recovery results are shown below.

| Effect | Lag | Exact driver selected | Unique top-1 correct |
|---:|---:|---:|---:|
| 0.5 SD | 15 min | 0.6750 | 0.7425 |
| 0.5 SD | 30 min | 0.3850 | 0.6625 |
| 0.5 SD | 60 min | 0.1150 | 0.2500 |
| 1.0 SD | 15 min | 0.8525 | 0.9450 |
| 1.0 SD | 30 min | 0.7900 | 0.8950 |
| 1.0 SD | 60 min | 0.2125 | 0.5950 |
| 1.5 SD | 15 min | 0.8525 | 0.9450 |
| 1.5 SD | 30 min | 0.9100 | 0.9700 |
| 1.5 SD | 60 min | 0.2825 | 0.8075 |

No distractor co-selection was observed in the aggregate injected cells. For an observed 0/400 distractor rate within an effect-lag cell, the Wilson upper 95% bound is approximately 0.0095; therefore the appropriate interpretation is that co-selection was rare under the registered audit, not impossible.

The difference between exact selection and top-1 ranking is scientifically informative. For example, under the registered 1.0-SD / 60-min condition, the true driver was the unique top-ranked candidate in 59.5% of trials but crossed the full promotion gate in only 21.25%. ASDE therefore often identified the most plausible candidate without treating that ranking as sufficient evidence for promotion.

This behavior is consistent with the intended design. The engine is not optimized to maximize the number of declared discoveries; it is designed to restrict promotion when the evidence budget, directionality, or multiplicity-controlled threshold is insufficient.

## E. Driver-Specific Heterogeneity and Background Hardness
Aggregate end-to-end recovery conceals substantial driver heterogeneity. At 1.0 robust SD, exact-driver selection by truth driver was:

| Hidden truth driver | 15 min | 30 min | 60 min |
|---|---:|---:|---:|
| CU01 temperature rise | 1.00 | 1.00 | 0.46 |
| SJ01 temperature fall | 1.00 | 0.99 | 0.25 |
| SJ01 humidity fall | 0.99 | 0.98 | 0.07 |
| SJ01 pressure rise | 0.42 | 0.19 | 0.07 |

A post-audit diagnostic showed that this heterogeneity is partly attributable to the unmodified real RF background around each atmospheric event family. Before any synthetic injection, CU01 temperature-rise events already exhibited a favorable post-versus-pre RF asymmetry within the short response horizon, whereas SJ01 pressure-rise events exhibited an adverse pre/post asymmetry. The benchmark therefore measures detection on a realistic structured background rather than homogeneous abstract noise.

This diagnostic was performed after the v21 audit and was not used to alter thresholds, driver definitions, or promotion rules. Results are therefore reported as an explanation of benchmark hardness rather than as a calibration step.

## F. Constrained AI Pilot: Safety Result
The prospective six-candidate AI pilot has completed its automated safety phase. Across RFATM-0001 through RFATM-0006, the constrained language-model outputs produced:
- zero detected fabricated numeric claims;
- zero detected validation/causality state overreach;
- zero references recommending access to D_validation;
- zero falsification-test families outside the registered vocabulary;
- SCREEN_OUT as the recommendation for all candidates that had already failed deterministic scientific gates.

These results support a narrow claim: the frozen constrained interface respected the registered safety contract in this six-candidate pilot. They do not establish that the model cannot hallucinate, and they do not yet establish incremental scientific value.

A blinded comparison against the deterministic B0 template has been generated with a cryptographic commitment to the hidden option mapping. Human utility scoring remains pending. Consequently, no claim that AI improves scientific reasoning is included in the current Results section, and the manuscript title remains conditional.

# VII. Discussion

## A. A Discovery Engine Should Be Judged by What It Rejects
The natural-data analysis illustrates why scientific-discovery systems should not be evaluated only by the number or apparent novelty of generated patterns. Each RFATM candidate was plausible under at least one exploratory view. Several exhibited attractive correlations, state enrichment, threshold robustness, or temporal structure. Yet none survived the complete sequence of replication, independence, directionality, multiplicity, and control requirements needed for hypothesis freezing.

From a conventional pattern-mining perspective, six rejected candidates may look unproductive. From a scientific-validity perspective, the attrition is informative: the workflow prevented multiple attractive exploratory findings from being converted into stronger claims than their evidence supported.

This distinction is especially relevant for AI-assisted research. Modern language models can generate large numbers of plausible explanations quickly. The bottleneck therefore shifts from hypothesis generation to disciplined elimination, evidence budgeting, and provenance-preserving validation.

## B. Screening Performance Is Not Discovery Performance
The known-driver and hidden-driver audits answer different questions. The first asks whether a frozen screening gate can recover a prespecified injected relationship while controlling empirical null detections. The second asks whether the same scientific logic can identify the generating driver among competing hypotheses.

The difference in performance between v12 and v21 is expected and important. A known-driver test does not pay the statistical and attribution cost of searching a hypothesis family. Once the driver is hidden, ASDE must control multiplicity across candidate drivers and response horizons and must contend with natural temporal overlap among candidate event families.

For this reason, the hidden-driver audit should be treated as the stronger evidence for the bounded discovery claim. Conversely, it should not be generalized into an open-ended AI-discovery claim: the library is finite, prespecified before the audit, and deliberately selected for temporal identifiability.

## C. Ranking and Scientific Promotion Are Different Operations
One of the clearest v21 results is the separation between top-1 ranking and gate-passing selection. At longer lags, the planted driver can frequently remain the best-ranked explanation while failing the multiplicity-controlled evidence threshold.

This distinction is desirable for a scientific workflow. Ranking answers, "which candidate currently looks best?" Promotion asks a stronger question: "is the evidence sufficient, under the registered decision rule, to advance this candidate in the scientific state machine?" ASDE deliberately permits the first answer to be positive while the second remains negative.

This design also clarifies the appropriate role of language models. A language model may help expand, organize, or critique candidate explanations, but it should not be given authority to convert ranking or narrative plausibility into validated scientific status.

## D. The Real Background Is Part of the Benchmark
Synthetic injection on a real field background has an advantage and a cost. It preserves nonstationarity, missingness patterns, natural RF events, and environmental structure that would be difficult to reproduce in white-noise or fully simulated data. However, candidate drivers do not encounter equivalent backgrounds.

The v22 diagnostic demonstrates this directly. Some event families start from a favorable post-event RF asymmetry, whereas others start from neutral or adverse asymmetry. Consequently, recovery is a joint property of the injected signal, the detector, the decision gate, and the structured background.

Rather than normalize this heterogeneity away after seeing the audit, ASDE reports per-driver recovery. Future multi-link evaluation should test whether similar background-hardness effects recur across environments.

## E. Morphology Robustness Defines an Operating Envelope
The v15 stress test prevents a broad interpretation of the strong v12 numbers. The primary composite detector is well matched to coherent multi-metric degradation. When only one RF subsystem is perturbed, the composite quality representation dilutes the signal. The exploratory multi-view extension partly recovers some sparse effects but introduces a larger multiplicity burden and does not dominate the primary detector.

This result argues against a single universal RF-degradation detector. A future ASDE version may use a preregistered family of physically interpretable RF views or hierarchical testing procedure, but such a redesign must be frozen and evaluated on new audit seeds or external data rather than tuned retrospectively on the current benchmark.

## F. What the AI Layer Does—and Does Not Do
ASDE is intentionally AI-assisted rather than AI-authoritative. The language model does not compute the reported p-values, confidence intervals, event counts, or benchmark metrics. It cannot alter the holdout, thresholds, multiplicity corrections, or candidate state.

Its proposed role is narrower: translate bounded evidence packets into scientific interpretations, alternative explanations, confounders, and falsification suggestions. This design reduces the surface area over which an LLM can silently modify evidence.

The safety pilot shows that the frozen interface can obey these boundaries across the six tested candidates. Whether the language model contributes enough incremental scientific utility to justify prominence in the title is intentionally left to blinded human evaluation. If that preregistered criterion is not met, ASDE remains scientifically intact as a deterministic auditable workflow and the AI layer will be described as optional.

## G. Reproducibility as Part of the Scientific Method
Git provenance is used not merely for software engineering but as part of the inferential record. Protocol freezes precede audit seeds, hashes bind results to source snapshots, failed candidates remain in the registry, and headline v21 metrics can be reconstructed from the stored trial table.

A one-command verifier checks the development snapshot, frozen protocol, audit artifacts, recorded package versions, headline metric reconstruction, and analytical isolation of the holdout. This does not eliminate every reproducibility problem, especially for stochastic language-model outputs, but it makes the deterministic scientific core independently inspectable.

# VIII. Limitations

First, the empirical field case comes from a single approximately 12-km rural high-altitude 6 GHz link. The current results do not establish generalization to other 6 GHz links, frequency bands, climates, terrains, radio vendors, or network architectures.

Second, the strongest benchmark results concern synthetic RF perturbations injected into a real background. Synthetic recovery quantifies the behavior of the discovery/screening machinery under registered ground-truth perturbations; it does not demonstrate that any natural atmospheric variable caused an RF degradation event.

Third, the v21 hidden-driver benchmark is bounded to four prespecified atmospheric drivers. The candidate library was developed adaptively on D_development through atmospheric-only identifiability analysis before its final freeze. The audit uses new reserved simulation seeds but the same physical background. The result therefore measures reproducibility under the frozen library, not independent replication on a new physical dataset.

Fourth, candidate event families remain temporally related. The final library satisfies the registered overlap rule, but the maximum pairwise overlap lies close to the admissibility boundary. Unique attribution may become harder in richer libraries with more strongly coupled atmospheric variables.

Fifth, the primary RF outcome is a composite of RSSI, SNR, and MCS. Post-audit morphology testing demonstrates reduced sensitivity to sparse subsystem-specific perturbations, and real-data outcome sensitivity shows that at least one exploratory context association depends on the RF event definition.

Sixth, circular-shift nulls preserve important aspects of event timing but cannot represent every possible form of nonstationarity or dependence. Future work should evaluate alternative dependence-aware null models and resampling procedures without using the current audit results for tuning.

Seventh, D_validation remains analytically embargoed from scientific analysis and candidate evaluation because no natural candidate met the freeze gate. This preserves the registered protection against post-selection bias but means that the present paper does not report an independently confirmed natural atmospheric–RF hypothesis.

Eighth, external configuration cohorts are registered but not yet used as confirmatory replication in this paper. Cross-configuration and cross-link replication remain future tests of generality.

Ninth, the AI-utility pilot is not yet complete at Draft v0. The constrained outputs passed automated safety checks, but incremental scientific utility relative to the deterministic baseline requires blinded human scoring. The final title and AI contribution statement will follow the preregistered result rather than being decided editorially after the fact.

# IX. Conclusion
ASDE addresses a methodological problem that becomes more important as automated systems make scientific candidate generation cheaper: plausible patterns can be generated faster than they can be validated. The workflow therefore treats discovery as a sequence of state transitions governed by evidence, not as a ranking problem.

On a real rural high-altitude 6 GHz measurement background, six natural atmospheric–RF candidates were screened out before confirmatory validation. A known-driver audit quantified the behavior of the statistical gate, while a stricter hidden-driver benchmark quantified recovery when the generating atmospheric hypothesis was concealed within a competing finite library. The results show both useful recovery and substantial limits, particularly at longer lags and for difficult background conditions.

The central methodological lesson is that an auditable discovery system should make it easy to generate candidates but difficult to promote them. AI may assist hypothesis formulation and criticism, but scientific status should remain tied to deterministic evidence, explicit multiplicity and temporal controls, protected validation data, reproducible provenance, and human scientific responsibility.

# Working Reference Key Map
The citation keys in Draft v0 are placeholders tied to verified sources. They will be converted to IEEE numbered references only after bibliographic metadata are independently checked.

- AI-SCIENTIST-2024 — Lu et al., The AI Scientist: Towards Fully Automated Open-Ended Scientific Discovery, arXiv:2408.06292.
- AI-SCIENTIST-V2-2025 — Yamada et al., The AI Scientist-v2: Workshop-Level Automated Scientific Discovery via Agentic Tree Search, arXiv:2504.08066.
- CO-SCIENTIST-2026 — Gottweis et al., Accelerating scientific discovery with Co-Scientist, Nature 655, 487–496, DOI 10.1038/s41586-026-10644-y.
- ROBIN-2026 — Ghareeb et al., A multi-agent system for automating scientific discovery, Nature 655, 497–505, DOI 10.1038/s41586-026-10652-y.
- POPPER-2025 — Huang et al., Automated Hypothesis Validation with Agentic Sequential Falsifications, ICML 2025, PMLR 267.
- CONTROLA-2025 — ControlA: Agentic Workflow Control Mechanisms for Reliable Science, IEEE eScience 2025, DOI 10.1109/eScience65000.2025.00086.
- REUSABLE-HOLDOUT-2015 — Dwork et al., The reusable holdout: Preserving validity in adaptive data analysis, Science 349(6248), DOI 10.1126/science.aaa9375.
- POST-SELECTION-2022 — Kuchibhotla, Kolassa, and Kuffner, Post-Selection Inference, Annual Review of Statistics and Its Application 9, DOI 10.1146/annurev-statistics-100421-044639.
- AI-SCIENTIST-PITFALLS-2025 — Luo, Kasirzadeh, and Shah, The More You Automate, the Less You See: Hidden Pitfalls of AI Scientist Systems, arXiv:2509.08713.
- TSAD-BENCHMARKS-2023 — Wu and Keogh, Current Time Series Anomaly Detection Benchmarks are Flawed and are Creating the Illusion of Progress, IEEE TKDE 35(3), DOI 10.1109/TKDE.2021.3112126.
- RADIO-DT-2025 — Moharam et al., Anomaly detection using machine learning and adopted digital twin concepts in radio environments, Scientific Reports, DOI 10.1038/s41598-025-02759-5.
- EQUI-MRNA-2025 — Yazdani-Jahromi, Khodabandeh Yalabadi, and Ozmen Garibay, Equi-mRNA: Protein Translation Equivariant Encoding for mRNA Language Models, arXiv:2508.15103.

- MESSER-2006 — Messer, Zinevich, and Alpert, Environmental monitoring by wireless communication networks, Science 312(5774), 713, DOI 10.1126/science.1120034.
- LEIJNSE-2007 — Leijnse, Uijlenhoet, and Stricker, Rainfall measurement using radio links from cellular communication networks, Water Resources Research 43(3), W03201, DOI 10.1029/2006WR005631.
- UIJLENHOET-2018 — Uijlenhoet, Overeem, and Leijnse, Opportunistic remote sensing of rainfall using microwave links from cellular communication networks, WIREs Water 5, e1289, DOI 10.1002/wat2.1289.
- SPACKOVA-2025 — Špačková, Fencl, and Bareš, Information-theoretic analysis of commercial microwave link and environmental variables in rainfall estimation, Atmospheric Measurement Techniques 18, 7445–7463, DOI 10.5194/amt-18-7445-2025.
