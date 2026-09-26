# ASDE AI Contribution Pilot — Blind Review Instructions

## Objective
Compare two candidate-critique outputs for each of six already-screened-out atmospheric–RF candidates. One option is produced by a deterministic baseline and one by a constrained language-model layer. Reviewer identity of the systems is blinded.

Do not attempt to infer which option is AI-generated. Score only scientific usefulness.

## Evidence
For each candidate, reviewers receive:
- pattern description;
- failed scientific gate;
- deterministic reason for failure;
- current status.

No D_validation values are included.

## Scoring
Score each option independently from 0 to 2 on five dimensions:

- **Interpretive completeness**
  - 0: misses or misstates the meaning of the failed gate.
  - 1: basically correct but incomplete.
  - 2: scientifically precise and complete.

- **Alternative-explanation usefulness**
  - 0: irrelevant, unsupported, or merely repeats the evidence.
  - 1: plausible but limited/redundant.
  - 2: provides useful nonredundant alternatives grounded in the evidence.

- **Falsifiability**
  - 0: no usable discriminating test.
  - 1: a plausible but underspecified test.
  - 2: concrete tests that could distinguish competing explanations.

- **Confounder coverage**
  - 0: ignores important plausible confounders.
  - 1: partial coverage.
  - 2: surfaces relevant confounders without unsupported speculation.

- **Actionability**
  - 0: does not help determine a scientifically legitimate next action.
  - 1: generally useful.
  - 2: clearly supports a legitimate next step while respecting the failed gate.

## Preference
After scoring both options, select A, B, or TIE. Also flag unsupported speculation separately for A and B.

## Blinding integrity
The option-to-system mapping is not stored in the repository during review. A SHA-256 commitment to the hidden mapping is stored in review_key_commitment.json. The exact mapping is held outside the repository and will be revealed only after reviewer forms are finalized.

## Reviewers
At least two domain-competent reviewers are required. Reviewer forms must be finalized before unblinding.

## Decision rule
The pilot's title-retention rule is defined in ASDE_AI_CONTRIBUTION_EVALUATION_PROTOCOL.md. No post-review change to that rule is allowed.
