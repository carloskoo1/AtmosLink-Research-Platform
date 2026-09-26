# IEEE ASDE Claim Ledger

## Rule
A manuscript claim is allowed only if it maps to a versioned artifact and stays within the registered scope. Stronger wording is prohibited even when it sounds reasonable.

| ID | Claim | Evidence | Authorized wording | Prohibited escalation |
|---|---|---|---|---|
| C1 | Known-driver screening false-positive behavior | v12 audit, 1000 circular-shift null trials | "The frozen screening gate produced an empirical family-wise false-positive rate of 2.5% (Wilson 95% CI 1.70–3.66%) under the registered null benchmark." | "ASDE guarantees a 2.5% false-positive rate" or universal Type-I error guarantee |
| C2 | Known-driver recovery | v12 audit | "For the registered joint RF perturbation family at 1.0 robust SD, recovery was 100%, 100%, and 94% at 15/30/60-min lags." | Generalization to arbitrary RF degradations |
| C3 | Safeguard ablation | v14 audit ablation | "The naive uncorrected rule yielded 7.9% empirical FPR versus 2.5% for the full frozen screening gate in the audit benchmark." | Claim that every ASDE safeguard is individually necessary unless separately ablated |
| C4 | Hidden-driver null control | v21 audit, frozen four-driver library, 1000 null trials | "Within the prespecified four-driver library, library-wide null FWER was 2.0% (Wilson 95% CI 1.30–3.07%)." | Open-ended discovery error guarantee |
| C5 | Hidden-driver exact selection | v21 audit | "At 1.0 robust SD, exact-driver selection was 85.25%, 79.0%, and 21.25% at 15/30/60-min lags." | "ASDE reliably discovers the true cause" |
| C6 | Hidden-driver ranking | v21 audit | "Unique top-1 ranking was 94.5%, 89.5%, and 59.5% at 15/30/60 min for the registered 1.0-SD condition." | Treat ranking as statistical selection or validation |
| C7 | Conservative gate behavior | v21 comparison of ranking vs selection | "At longer lags the true driver may rank first while still failing the frozen promotion gate, illustrating deliberate conservatism." | Claim that every non-promoted top-ranked driver is scientifically true |
| C8 | Distractor co-selection | v21 audit | "No distractor co-selection was observed in the aggregate audited injected cells; for 0/400 events per cell the Wilson upper bound is approximately 0.95%." | "Distractor selection is impossible" |
| C9 | Driver heterogeneity | v22 post-audit diagnostic | "End-to-end recovery varies with natural background structure surrounding different atmospheric event families." | Retrospectively alter v21 thresholds to equalize driver difficulty |
| C10 | Morphology operating envelope | v15 exploratory stress | "Post-audit stress testing shows materially lower sensitivity for some single-subsystem and longer-lag/gradual perturbations." | Apply v12 recovery rates to all degradation morphologies |
| C11 | Multi-view remedy | v16b exploratory | "A multi-view extension preserved low empirical null detection but did not uniformly recover sparse-subsystem effects; it was not adopted as the primary detector." | Present multi-view as a solved robustness improvement |
| C12 | Natural-data candidates | candidate registry v1–v6 | "Six candidate atmospheric–RF patterns were screened out before confirmatory validation." | "Six discoveries were made" |
| C13 | CTX-0001 | v6 + v16 outcome sensitivity | "CTX-0001 is an exploratory, outcome-definition-sensitive context association." | "CTX-0001 is a precursor, predictor, causal effect, or validated marker" |
| C14 | Natural atmospheric causality | none | No positive causal claim is authorized. | Any statement that weather caused the observed RF degradation in DISCOVERY-001 |
| C15 | D_validation isolation | holdout isolation audit | "The 716-observation D_validation block has remained analytically isolated from candidate selection, tuning, screening, and benchmark development." | "Never read", "never opened", or claims about raw-byte access history |
| C16 | Reproducibility | environment manifest, SHA-256 artifacts, v21 verifier | "Headline audit results can be reconstructed from versioned trial artifacts under the recorded environment and verified hashes." | "Fully reproducible everywhere" before DOI/archive and independent rerun |
| C17 | AI safety constraints | A1 safety audit across RFATM-0001–0006 | "In the frozen six-candidate pilot, the constrained A1 outputs produced zero detected numeric-fabrication, state-overreach, holdout-reference, or unapproved-test-family violations." | "The language model cannot hallucinate" or general safety claim |
| C18 | AI incremental value | blinded pilot pending | Not yet authorized. | "AI improves scientific reasoning" before blinded human review |
| C19 | Novelty / contribution scope | comparator matrix + literature search log | "The paper contributes an implemented and quantitatively evaluated validity-constrained instantiation for bounded scientific inference on autocorrelated environmental–RF field telemetry, including frozen screening and hidden-driver audits, event-level temporal falsification, failure-mode stress testing, and natural candidate attrition." | Claims that ASDE invents validation gates, scientific state machines, structurally enforced multiplicity control, protected validation, claim-to-evidence provenance, Git-like research protocols, human–AI hypothesis construction, statistically supported LLM hypotheses, agentic wireless AI, holdout protection, synthetic injection, or environmental sensing; and any "first", "unique", or "unprecedented" wording |
| C20 | Cross-link generalization | single AtmosLink physical link | "The current empirical case study is one rural high-altitude 6 GHz link." | Generalization to all 6 GHz, microwave, high-altitude, or rural links |
| C21 | Independent event support | v21 frozen library + independent_event_support.csv | "The four frozen drivers contain 23–28 refractory events total, with 5–8 events represented in each contiguous development fold." | Treat 2860 development rows as independent inferential units or claim complete independence between atmospheric event families |

## Manuscript enforcement
Before submission, every sentence in Abstract, Contributions, Results conclusions, Discussion and Conclusion that contains a quantitative, causal, novelty, validation or generalization claim must map to one or more Claim IDs above.

Any new result requires a new ledger entry before it can be promoted into manuscript prose.
