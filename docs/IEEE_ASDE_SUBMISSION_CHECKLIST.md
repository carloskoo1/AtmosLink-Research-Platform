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
1. preserve the current non-AI title and treat the existing A1-vs-B0 comparison as safety/feasibility only; a new AI-utility study is not required for this paper;
2. complete the structured novelty search in IEEE Xplore and Scopus/Web of Science (or equivalent institutional databases), including backward/forward citation chasing and version/retraction checks;
3. create the DOI-bearing immutable archive and manuscript tag;
4. run the full manuscript against IEEE_ASDE_CLAIM_LEDGER.md and the integrated Meta-Reviewer audit;
5. preserve Reviewer A's boundary: v21/v23 are conditional historical benchmarks; v24 is a prospective calibration design and field-wide Type-I/FWER claims remain prohibited unless v24 or equivalent independent calibration succeeds;
6. preserve Reviewer B's boundary: bounded operational-telemetry Methods claims only; no natural fade, propagation mechanism, encoded-MCS physical severity, or cross-link transportability claim;
7. preserve Reviewer C's boundary: bounded hidden-driver attribution, non-AI title, no generic AI-scientist novelty claim;
8. references checked for accuracy/retraction status;
9. AI-generated-text disclosure finalized under the then-current IEEE Access policy;
10. final Word/LaTeX and PDF content verified identical.

### v24 timing decision
Completion of v24 is **not logically required** for a manuscript whose claims remain restricted to conditional benchmark operating characteristics and explicitly disclaim field-wide calibration. However, the absence of prospective N1 calibration remains the strongest plausible Reviewer-A major-revision vector. If schedule permits, the Meta-Reviewer recommends completing v24 before submission to materially reduce statistical-review risk.
