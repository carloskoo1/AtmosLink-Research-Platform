# IEEE Access — ASDE Submission Checklist

Verified against the IEEE Access author guidance on 2026-09-26.

## Manuscript type
Primary planned type: **Methods**.

IEEE Access describes a Methods article as reporting a new or improved fabrication/manufacturing technique, or a new experimental, measurement or mathematical technique, with the focus on the method rather than the practical system alone.

## Format
- Required IEEE Access template.
- Double-column, single-spaced manuscript.
- Submit source file (Word or LaTeX) and matching PDF.
- All authors and required biographies included.
- Minimum 3 and maximum 10 submission keywords.

## Length
IEEE Access has no general page limit, but currently strongly recommends keeping articles under approximately 20 pages for readability. Longer manuscripts may require a pre-submission inquiry depending on circumstances. Detailed simulation grids should therefore be moved to supplementary material where possible.

## Technical acceptance criteria relevant to ASDE
- clear advance over existing knowledge;
- experiments/statistics/analyses performed to a high technical standard;
- sufficient methodological detail;
- conclusions supported by data;
- accurate and relevant prior-work references.

## AI-generated content disclosure
IEEE requires AI-generated content used in an article to be disclosed in the Acknowledgments. The AI system must be identified and the paper sections using AI-generated content should be identified, with a brief explanation of the level of use.

ASDE manuscript policy:
- disclose ChatGPT / GPT-5.6 Sol use where text/code/content was AI-generated;
- distinguish manuscript-assistance use from the scientific AI layer being studied;
- authors remain responsible for every scientific claim, reference, statistic and code artifact;
- no AI-generated reference enters the bibliography without independent verification.

## Reproducibility
IEEE Access encourages:
- detailed methodology;
- online data repositories;
- online code repositories;
- executable-code services such as Code Ocean;
- participation in the IEEE Access Reproducibility Initiative.

ASDE already has:
- versioned Git provenance;
- frozen protocols;
- SHA-256 dataset/result manifests;
- environment/package pins;
- one-command artifact verification;
- raw audit trial tables and reconstructed headline metrics.

Still required before submission:
- DOI-bearing immutable archive of releasable code/data/results;
- manuscript tag matching the archived release;
- explicit data-availability statement describing any field data that cannot be publicly released.

## Final internal gates
Before submission:
1. blinded AI-utility pilot completed and title rule applied;
2. structured novelty search completed;
3. DOI archive created;
4. full manuscript checked against IEEE_ASDE_CLAIM_LEDGER.md;
5. Reviewer A statistical **PASS** required for field-wide FWER claims; Reviewer B RF audit **PASS** required for physically calibrated RF sensitivity or mechanism claims. Both remain OPEN (Major). A narrower conditional Methods submission would require a documented scope decision, renewed adversarial review and explicit acceptance of both limitations. Reviewer C audit and Meta-Reviewer adjudication remain pending;
6. references checked for accuracy/retraction status;
7. AI disclosure finalized;
8. final Word/LaTeX and PDF content verified identical.
