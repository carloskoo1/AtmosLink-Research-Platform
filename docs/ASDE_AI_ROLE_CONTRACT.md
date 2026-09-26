# ASDE AI Role Contract

## Principle
ASDE is AI-assisted, not AI-authoritative. The language model may expand the search space and translate computed evidence into candidate hypotheses; it cannot create, modify, or certify statistical evidence.

## Allowed AI actions
1. Read a bounded, machine-generated evidence packet.
2. Describe a candidate pattern in scientific language.
3. Propose alternative mechanistic interpretations and explicit confounders.
4. Propose falsification tests from an approved test vocabulary.
5. Classify novelty provisionally as KNOWN_EXPECTED, CONTEXTUALLY_INTERESTING, UNUSUAL, or LITERATURE_REVIEW_REQUIRED.
6. Produce a hypothesis candidate with clearly stated antecedent, response, lag/horizon, and falsification criterion.
7. Critique a candidate and recommend SCREEN_OUT or HUMAN_REVIEW; it cannot directly promote status.

## Prohibited AI actions
1. Invent or estimate p-values, confidence intervals, effect sizes, event counts, or timestamps.
2. Change frozen thresholds, QC exclusions, holdout boundaries, multiplicity rules, or validation criteria.
3. Read D_validation before a frozen hypothesis authorizes access.
4. Label a pattern CONFIRMED, VALIDATED, CAUSAL, or SCIENTIFICALLY_PROVEN.
5. Remove failed candidates from provenance.
6. Choose only favorable subsets after seeing outcomes.
7. Convert a context marker into a precursor without a registered directionality test.

## Evidence packet boundary
The AI receives computed summaries rather than unrestricted raw time-series access whenever possible. Every numeric field must carry provenance to a deterministic script output.

Minimum evidence packet:
- experiment_id and candidate_id;
- source dataset hash and Git commit;
- development interval and configuration;
- QC eligibility statement;
- feature definitions;
- independent event count;
- effect estimate and uncertainty if computed;
- pre/post directionality results;
- multiplicity-adjusted statistics where applicable;
- temporal-fold consistency;
- negative-control results;
- known operational confounders;
- current state-machine status.

## Promotion authority
Only deterministic gates + human scientific review may cause:
CANDIDATE -> HYPOTHESIS -> FROZEN -> VALIDATING.

The language model can never execute the state transition by prose alone.

## Paper claim
The AI contribution should be described as constrained hypothesis-space exploration, structured criticism and hypothesis formulation operating on auditable evidence packets. Statistical validation and state promotion are implemented by deterministic, versioned procedures.
