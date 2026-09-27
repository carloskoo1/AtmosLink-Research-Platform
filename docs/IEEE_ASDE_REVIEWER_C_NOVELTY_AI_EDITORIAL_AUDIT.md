# IEEE ASDE — Reviewer C: Novelty, AI-for-Science, and Editorial Audit

**Role:** adversarial reviewer focused on novelty, AI-for-science positioning, benchmark semantics, and IEEE Access editorial threshold.

**Current disposition:** **DESIGN PASS / FINAL NOVELTY SEARCH & SUBMISSION COMPLIANCE PENDING.**

The initial audit found the manuscript technically substantive enough to remain publishable as an applied Methods / experimental-methodology article, but judged the then-current AI/scientific-discovery framing broader than the evidence supported. The manuscript has since been revised so that the deterministic, falsification-oriented environmental–RF workflow is the primary contribution and the LLM layer is secondary unless a future fairer prospective utility study demonstrates incremental value.

## C1. AI is not yet a demonstrated core contribution — Major

The deterministic scientific core performs:
- candidate-state control;
- QC eligibility;
- temporal event construction;
- multiplicity correction;
- hidden-driver selection;
- benchmark execution;
- provenance checks;
- holdout isolation;
- candidate screening.

None of the headline v12/v21/v23/v24 results requires the LLM.

The frozen A1 safety pilot demonstrates boundary compliance on six already-screened candidates, but human incremental-utility scoring remains pending. Therefore the manuscript currently demonstrates **safe bounded use**, not scientific value added by AI.

### Required action
Until incremental utility is established under a fair comparator, the default manuscript title should be the non-AI route:

**ASDE: An Auditable Workflow for Hypothesis Screening in Long-Duration Environmental–Radio Telemetry**

The language-model layer may remain a secondary Methods component.

## C2. The current AI utility pilot has an output-budget confound — Major

The deterministic B0 baseline and A1 output do not have matched expressive capacity.

Across RFATM-0001–0006:
- B0 always provides 2 alternative explanations and 2 falsification tests;
- A1 always provides 3 alternative explanations and 3 falsification tests;
- mean total textual payload is approximately 477 characters for B0 versus 1185 for A1.

Thus a blinded preference for A1 could partly measure **more content opportunity**, not better scientific reasoning.

The existing pilot remains valid for its automated safety endpoints, because those do not depend on prose richness. It is not a strong confirmatory test of incremental scientific utility.

### Required action
Do not use the current blinded utility result, even if favorable, as the sole basis for title-level AI prominence.

If an AI-utility claim is desired, preregister a new pilot with:
- matched output slots;
- matched maximum token/character budget;
- identical allowed falsification vocabulary;
- equal evidence packets;
- ideally an expert-authored or stronger structured non-LLM comparator in addition to B0;
- evaluation on more than only already-screened candidates.

## C3. v21 is bounded hidden-driver attribution, not open-ended scientific discovery — Major

The v21 benchmark hides one planted truth inside a finite four-driver prespecified library. This is stronger than known-driver screening but remains a bounded attribution/selection task.

Recent scientific-discovery benchmarks make this distinction explicit. TruthInsightBench separates execution/recovery of a hidden target from open-ended discovery by withholding expected conclusions and analysis paths. SDABench similarly distinguishes exploratory, inferential, predictive, causal, and mechanistic scientific capabilities.

### Required action
Rename the manuscript-level interpretation of v21 from a generic "end-to-end discovery benchmark" to:

**bounded hidden-driver attribution audit**

or equivalent.

Allowed:
- "evaluates a bounded discovery workflow";
- "tests driver attribution within a prespecified hypothesis family";
- "quantifies exact selection, abstention, and distractor control."

Not allowed:
- "demonstrates open-ended scientific discovery";
- "validates autonomous discovery";
- "shows that ASDE discovers the true cause."

## C4. Abstention, evidence maturity, falsification and insufficient-evidence handling are active prior art — Major for novelty wording, not for technical validity

Recent benchmarks and systems already evaluate:
- open-ended scientific analysis;
- hypothesis validation;
- insufficient evidence / non-verifiable cases;
- controls and robustness;
- falsifiability;
- abstention competence;
- evidence-grounded scientific claims.

Relevant comparator families now include:
- TruthInsightBench (2026);
- SDABench (2026);
- BioDSA-1K (2025);
- BLADE (2024);
- EXPERIGEN (2026);
- abstention-aware agent benchmarks (2026);
in addition to AI Scientist, Co-Scientist, Robin, POPPER, THREAD-Bio, Sargsyan, PROV-AGENT, XScientist and related work already registered.

### Required action
ASDE must not claim novelty from:
- abstention itself;
- negative candidate attrition itself;
- evidence maturity;
- falsifiability as a general concept;
- AI hypothesis generation/critique;
- hidden-target scientific benchmarks;
- real-data scientific-agent evaluation.

The contribution must remain domain- and implementation-specific.

## C5. The strongest defensible novelty is empirical and methodological, not architectural — Major but survivable

The paper's defensible contribution is the combination of:
1. an operational high-altitude environmental–RF field platform;
2. a documented adaptive scientific history rather than a clean retrospective benchmark;
3. event-level temporal hypothesis screening under autocorrelation and observation asymmetry;
4. explicit retention of failed candidates and post-audit failures;
5. frozen known-driver and bounded hidden-driver audits on the real telemetry background;
6. gate ablation showing that some proposed safeguards were redundant;
7. morphology/outcome/observability stress tests that reduce rather than inflate claims;
8. pre-freeze prospective calibration design created in response to identified inferential defects;
9. hash-bound, executable provenance.

This is an **evaluation of a validity-constrained scientific workflow in a difficult field-telemetry domain**.

It is not a new generic AI-scientist architecture.

## C6. The paper remains plausible for IEEE Access if framed as applied experimental methodology — Not fatal

IEEE Access explicitly accepts applications-oriented work, new experiments or measurement techniques, and negative results when technically sound, clearly described and of interest to IEEE readers.

Therefore domain specificity is not itself fatal. A manuscript can be publishable without inventing a new AI architecture if the applied experimental methodology, measurement setting, quantitative audit, and reproducibility package constitute original work of technical interest.

### Editorial implication
The strongest category is **Research Article / applied Methods**, not "new AI architecture".

The Introduction and Conclusion should foreground:
- the environmental–RF inferential problem;
- why conventional row-level association is unsafe;
- what was actually measured and falsified;
- what the benchmark revealed about false selection and gate redundancy;
- how the methodology is reproducibly instantiated.

AI should not occupy the first sentence of the novelty argument.

## C7. Reviewer C would challenge the ASDE name/title if "discovery" is left undefined — Major wording risk

"Scientific discovery" can mean:
- open-ended hypothesis invention;
- bounded hypothesis search;
- scientific analysis workflow;
- hypothesis screening and falsification.

ASDE currently spans these senses.

### Required action
Define the manuscript's operational meaning explicitly:

> In this paper, "discovery workflow" denotes the process from adaptive candidate generation through falsification and bounded hypothesis screening; it does not imply autonomous open-ended discovery or causal identification.

For the title, Reviewer C prefers the narrower formulation:

**ASDE: An Auditable Workflow for Hypothesis Screening in Long-Duration Environmental–Radio Telemetry**

Alternative if "discovery" is retained:

**ASDE: Auditable Falsification for Bounded Scientific Discovery in Environmental–Radio Telemetry**

## C8. Negative candidate attrition is valuable evidence but not a novelty primitive — Minor/Major boundary

Rejecting six plausible candidates is scientifically informative because it demonstrates how weaker analyses would have overclaimed.

However, negative results and failed hypotheses are not novel by themselves.

### Required action
Present attrition as **empirical evidence about workflow behavior**, not as an architectural innovation.

## C9. v23 strengthens the paper precisely because it weakens the architecture — Strength

The v23 result that M1, M2 and M3 made identical finite-library selections is editorially valuable. It demonstrates that the authors did not preserve complexity merely to defend ASDE.

Reviewer C views this as a credibility strength:
- multiplicity correction had demonstrated incremental effect;
- later gates did not in that benchmark;
- the manuscript explicitly says so.

Retain this result prominently.

## C10. v24 is evidence of methodological self-correction, not yet a result — Strength with claim boundary

The v24 pre-freeze design responds to identified weaknesses in observation symmetry, support calibration and physical-null interpretation.

This is useful as reproducible methodology development, but prospective v24 outcomes do not yet exist.

### Required action
Do not let the manuscript imply that v24 has solved field calibration. At submission before v24 completion, describe it as a preregistered prospective validation/calibration protocol or place detailed v24 material in Supplementary/Repository artifacts.

## C11. Reproducibility is a genuine editorial asset — Strength

The code/protocol/result hashing, reconstruction scripts, negative-candidate registry and refusal barriers align well with IEEE Access's emphasis on reproducibility and code availability.

This should be presented as a reproducibility strength, not a novelty claim that provenance itself is new.

## C12. AI-generated manuscript text creates a submission-compliance requirement — Major editorial action

IEEE Access currently requires disclosure of AI-generated text in the acknowledgements and citation to the AI system in sections that use AI-generated text.

Because AI has materially assisted manuscript drafting and editing, a submission-ready version must include the required disclosure and conform to the then-current IEEE policy.

This is an editorial-compliance requirement, not a scientific-result claim.

# Reviewer C decision matrix

| Question | Current judgment |
|---|---|
| Is the deterministic Methods contribution technically nontrivial? | **Yes** |
| Is a new generic AI-scientist architecture demonstrated? | **No** |
| Is incremental AI scientific utility demonstrated? | **No — safety only; utility pilot confounded/pending** |
| Does v21 demonstrate open-ended discovery? | **No — bounded hidden-driver attribution** |
| Is the environmental–RF field application original enough to remain viable? | **Potentially yes** |
| Are negative results / gate failures useful? | **Yes, as empirical evidence** |
| Is "AI-Assisted" currently justified in the title? | **No** |
| Is the paper fatally unpublishable? | **No** |
| Reviewer C current decision | **MAJOR REVISION** |

# Conditions for Reviewer C DESIGN PASS

Reviewer C can move from MAJOR REVISION to DESIGN PASS when:

1. the non-AI title is made the default current title;
2. v21 is consistently described as bounded hidden-driver attribution, not open-ended discovery;
3. the contribution list is rewritten around field methodology and quantitative evaluation rather than architectural novelty;
4. TruthInsightBench, SDABench, BioDSA/BLADE-class benchmarks and abstention literature are added to the comparison boundary;
5. the current A1-vs-B0 pilot is explicitly downgraded to safety/feasibility for title purposes, or replaced by a fairer prospective utility pilot;
6. the operational meaning of "scientific discovery" is defined in the manuscript;
7. IEEE AI-generated-text disclosure is added to the submission checklist;
8. no "first", "unique", "novel architecture", or generic AI-scientist superiority claim appears.

# Provisional editorial recommendation

Proceed with the paper, but pivot its center of gravity:

**FROM:** AI-assisted scientific discovery engine.

**TO:** reproducible, falsification-oriented hypothesis screening and methodological self-audit for autocorrelated environmental–RF field telemetry.

The AI layer can remain scientifically interesting, but the paper should not depend on it for publication.

# Reviewer C closure update

The manuscript and governance artifacts were revised after the initial MAJOR REVISION verdict.

## Conditions now satisfied

1. Non-AI title adopted. Current working title: ASDE: An Auditable Workflow for Hypothesis Screening in Long-Duration Environmental–Radio Telemetry.

2. v21 scope narrowed. Methods and Results now call v21 a Bounded Hidden-Driver Attribution Audit. The Discussion states that it does not constitute evidence of open-ended scientific discovery.

3. Contribution list re-centered. The primary contribution is the applied, quantitatively audited environmental–RF Methods workflow. The LLM interface is secondary.

4. Reviewer-C comparator boundary expanded. TruthInsightBench, SDABench, BioDSA-1K, BLADE, EXPERIGEN, and abstention-competence work were added to the working bibliography, comparator matrix, novelty matrix, and literature-search log.

5. AI utility claim reduced. The current A1-vs-B0 comparison is retained for safety/feasibility only because output opportunities are unequal. It cannot justify title-level AI prominence.

6. Operational meaning of discovery defined. The manuscript explicitly states that discovery workflow denotes the broader process from adaptive candidate generation through falsification and bounded screening, not autonomous open-ended discovery or causal identification.

7. IEEE AI-use compliance artifact created. A submission-time disclosure draft and checklist are stored in IEEE_ASDE_AI_USE_DISCLOSURE_DRAFT.md.

8. Automated manuscript audit hardened. The claim auditor now requires the non-AI title, bounded-attribution terminology, the AI-value limitation, field-wide error-control limitation, and prohibits open-ended-discovery benchmark overclaim.

## Mechanical verification

- Citation audit: PASS, 31 used keys / 31 BibTeX keys, no missing or unused entries.
- Manuscript claim audit: PASS, zero errors, zero warnings.

## Remaining Reviewer C conditions before submission

Reviewer C does not identify a remaining design-level novelty/AI objection that requires another adaptive analysis on D_development.

The remaining conditions are external/editorial:

- complete structured searches in IEEE Xplore and Scopus/Web of Science (or equivalent institutional databases) plus backward/forward citation chasing;
- re-check all very recent 2026 preprints for publication/version updates before submission;
- verify that no cited reference has been retracted;
- apply the then-current IEEE Access AI-generated-text disclosure and citation policy;
- create the DOI-bearing immutable artifact release;
- preserve the non-AI title unless a new, fair, prospectively frozen AI-utility study independently supports a stronger claim.

## Reviewer C interpretation

DESIGN PASS means the current manuscript no longer depends on a generic AI-scientist novelty claim and no longer presents bounded hidden-driver attribution as open-ended discovery.

It does not mean the literature search is exhaustive or that the final submission is cleared. Novelty remains a negative-search problem until the final structured database search is complete.
