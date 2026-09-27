#!/usr/bin/env python3
from pathlib import Path
import json,re,subprocess

ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
DRAFT=ROOT/"docs/IEEE_ASDE_FULL_DRAFT_V1.md"
CDOC=ROOT/"docs/IEEE_ASDE_REVIEWER_C_NOVELTY_AI_EDITORIAL_AUDIT.md"
BIB=ROOT/"docs/IEEE_ASDE_REFERENCES_WORKING.bib"
DISC=ROOT/"docs/IEEE_ASDE_AI_USE_DISCLOSURE_DRAFT.md"
AI_AUDIT=ROOT/"Results/scientific_discovery/DISCOVERY-001/reviewer_c_ai_comparator_audit.json"
OUT=ROOT/"Results/scientific_discovery/DISCOVERY-001/reviewer_c_novelty_ai_editorial_audit.json"

text=DRAFT.read_text(encoding="utf-8")
ctext=CDOC.read_text(encoding="utf-8")
bib=BIB.read_text(encoding="utf-8")
errors=[]
warnings=[]

# Current manuscript route must be non-AI and bounded.
required=[
    "ASDE: An Auditable Workflow for Hypothesis Screening in Long-Duration Environmental–Radio Telemetry",
    "## B. Bounded Hidden-Driver Attribution Audit",
    "## D. Bounded Hidden-Driver Attribution Audit",
    "incremental scientific value is not established",
    "does not constitute evidence of open-ended scientific discovery",
]
for s in required:
    if s not in text:
        errors.append(f"missing required Reviewer-C wording: {s}")

front=text[:8000]
if "AI-Assisted Scientific Discovery" in front:
    errors.append("AI-Assisted title/framing remains in active front matter")
if "## Conditional title" in front:
    errors.append("obsolete conditional title remains active")
if re.search(r"(?<!verification-)\b(first|unique|unprecedented)\s+(AI|scientific|discovery|workflow|framework|system)",text,re.I):
    errors.append("unqualified priority claim detected")

# New benchmark comparators must be cited in manuscript and BibTeX.
keys=["TRUTHINSIGHT-2026","SDABENCH-2026","BIODSA-2025","BLADE-2024","EXPERIGEN-2026","ABSTENTION-2026"]
for k in keys:
    if f"[{k}" not in text and f", {k}" not in text and f"{k}]" not in text:
        errors.append(f"Reviewer-C comparator not cited in manuscript: {k}")
    if ("{"+k+",") not in bib:
        errors.append(f"Reviewer-C comparator missing from BibTeX: {k}")

# AI comparator audit must prove mismatch and prohibit utility claim.
if not AI_AUDIT.exists():
    errors.append("AI comparator audit missing")
else:
    a=json.loads(AI_AUDIT.read_text())
    if a.get("status")!="PASS": errors.append("AI comparator audit not PASS")
    interp=a.get("interpretation",{})
    if interp.get("matched_alternative_slots") is not False:
        errors.append("AI comparator alternatives unexpectedly matched")
    if interp.get("matched_test_slots") is not False:
        errors.append("AI comparator test slots unexpectedly matched")
    if interp.get("utility_claim_authorized") is not False:
        errors.append("AI utility claim unexpectedly authorized")
    s=a.get("summary",{})
    if s.get("B0",{}).get("mean_alternative_explanations")!=2:
        errors.append("B0 alternative-slot audit changed")
    if s.get("A1",{}).get("mean_alternative_explanations")!=3:
        errors.append("A1 alternative-slot audit changed")

# Reviewer-C governance and disclosure.
if "DESIGN PASS / FINAL NOVELTY SEARCH & SUBMISSION COMPLIANCE PENDING" not in ctext:
    errors.append("Reviewer C disposition not DESIGN PASS")
if not DISC.exists():
    errors.append("IEEE AI-use disclosure draft missing")
if "AI-generated text" not in DISC.read_text(encoding="utf-8"):
    warnings.append("disclosure draft does not literally contain 'AI-generated text'")

# Historic snapshots may retain old language, but current draft/risk/ledger must be clean.
for rel in ["docs/IEEE_ASDE_REVIEWER_RISK_REGISTER.md","docs/IEEE_ASDE_CLAIM_LEDGER.md","docs/IEEE_ASDE_NOVELTY_MATRIX.md"]:
    t=(ROOT/rel).read_text(encoding="utf-8")
    if rel.endswith("REVIEWER_RISK_REGISTER.md") and "Reviewer C is **MAJOR REVISION**" in t:
        errors.append("risk register still marks Reviewer C MAJOR REVISION")

result={
    "reviewer":"C",
    "status":"PASS" if not errors else "FAIL",
    "disposition":"DESIGN PASS / FINAL NOVELTY SEARCH & SUBMISSION COMPLIANCE PENDING" if not errors else "OPEN",
    "errors":errors,
    "warnings":warnings,
    "ai_comparator_artifact":str(AI_AUDIT.relative_to(ROOT)),
    "comparators_checked":keys
}
OUT.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print(json.dumps(result,indent=2))
raise SystemExit(0 if not errors else 1)
