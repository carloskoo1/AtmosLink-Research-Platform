#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,subprocess,sys

ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
OUT=ROOT/"Results/scientific_discovery/DISCOVERY-001/meta_reviewer_audit.json"

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def run(script):
    r=subprocess.run([sys.executable,str(ROOT/script)],cwd=ROOT,text=True,capture_output=True)
    return {"script":script,"returncode":r.returncode,"stdout":r.stdout.strip(),"stderr":r.stderr.strip()}

errors=[]
warnings=[]
checks=[]

# Existing machine audits.
for script in [
    "scripts/audit_ieee_asde_citations.py",
    "scripts/audit_ieee_asde_manuscript_v1.py",
    "scripts/audit_asde_reviewer_c.py",
    "scripts/audit_asde_v24_code_concordance.py",
    "scripts/verify_asde_publication_artifacts.py",
]:
    r=run(script)
    checks.append(r)
    if r["returncode"]!=0:
        errors.append(f"failed audit: {script}")

# Reviewer dispositions.
A=(ROOT/"docs/IEEE_ASDE_REVIEWER_A_STATISTICAL_AUDIT.md").read_text(encoding="utf-8")
B=(ROOT/"docs/IEEE_ASDE_REVIEWER_B_RF_AUDIT.md").read_text(encoding="utf-8")
C=(ROOT/"docs/IEEE_ASDE_REVIEWER_C_NOVELTY_AI_EDITORIAL_AUDIT.md").read_text(encoding="utf-8")
R=(ROOT/"docs/IEEE_ASDE_REVIEWER_RISK_REGISTER.md").read_text(encoding="utf-8")
M=(ROOT/"docs/IEEE_ASDE_FULL_DRAFT_V1.md").read_text(encoding="utf-8")

if "DESIGN PASS / PROSPECTIVE CALIBRATION PENDING" not in A:
    errors.append("Reviewer A integrated disposition missing")
if "RESOLVED FOR BOUNDED METHODS CLAIMS ONLY" not in B:
    errors.append("Reviewer B bounded disposition missing")
if "DESIGN PASS / FINAL NOVELTY SEARCH & SUBMISSION COMPLIANCE PENDING" not in C:
    errors.append("Reviewer C integrated disposition missing")

# Current governance must not retain stale open-state labels.
stale=[
    "Reviewer A remains **OPEN (Major)**",
    "**OPEN (Major), Reviewer A**",
    "**Major wording risk; fix required**",
    "Reviewer C is **MAJOR REVISION**",
]
for s in stale:
    if s in R:
        errors.append(f"stale risk-register status: {s}")

# Current manuscript scope boundaries.
required_manuscript=[
    "An Auditable Workflow for Hypothesis Screening",
    "Bounded Hidden-Driver Attribution Audit",
    "does not constitute evidence of open-ended scientific discovery",
    "Results do not establish field-wide error control",
    "incremental scientific value is not established",
]
for s in required_manuscript:
    if s not in M:
        errors.append(f"manuscript scope boundary missing: {s}")

# Reviewer B fixed artifacts.
b_hashes={
    "Results/scientific_discovery/DISCOVERY-001/reviewer_b_field_functional.json":
        "ee94c82d7a520446ef6dcd33d4f25ba278a0ea94323b0399d189f639f9583bbe",
    "Results/scientific_discovery/DISCOVERY-001/v25_reviewer_b_analog_stress/trials.csv":
        "efb013c13ee0c868f07313b29b988f44cdeaf560a2cbb5caa307617a0aa8ca72",
    "Results/scientific_discovery/DISCOVERY-001/v25_reviewer_b_analog_stress/metrics.csv":
        "9d212810c49d176b9fee0330ca1a1e9904096aaa394dd123caf5aa503c1dcf0c",
    "Results/scientific_discovery/DISCOVERY-001/v25_reviewer_b_analog_stress/summary.json":
        "8d5365feb7ae9ccb6d039d814200b6a48496ed1132b6f9a0b553b5018af7ed00",
}
b_actual={}
for rel,expected in b_hashes.items():
    p=ROOT/rel
    if not p.exists():
        errors.append(f"Reviewer B artifact missing: {rel}")
        continue
    got=sha256(p); b_actual[rel]=got
    if got!=expected:
        errors.append(f"Reviewer B artifact hash mismatch: {rel}")

# v24 pre-freeze must remain inactive.
v24=ROOT/"Results/scientific_discovery/DISCOVERY-001/reviewer_a_v24_code_concordance.json"
if not v24.exists():
    errors.append("v24 prefreeze concordance artifact missing")
else:
    obj=json.loads(v24.read_text())
    if obj.get("status")!="PASS":
        errors.append("v24 prefreeze concordance not PASS")
    # Nested validator/runner strings are retained for provenance.
    tv=obj.get("template_validator_stdout","")
    rr=obj.get("runner_refusal_stdout","")
    if '"prospective_execution_authorized": false' not in tv:
        errors.append("v24 template does not prove inactive execution")
    if '"status": "REFUSED"' not in rr:
        errors.append("v24 runner refusal evidence missing")

# External blockers are expected and make submission_ready false without failing technical scope.
external_blockers=[]
if "structured novelty search" in R.lower() or "structured IEEE Xplore/Scopus" in R:
    external_blockers.append("final_structured_novelty_search")
if "DOI-bearing immutable" in R:
    external_blockers.append("doi_bearing_immutable_release")
if "AI-generated-text disclosure" in R or "AI-text disclosure" in R:
    external_blockers.append("final_ieee_ai_disclosure")
if "references checked for accuracy/retraction status" in (ROOT/"docs/IEEE_ASDE_SUBMISSION_CHECKLIST.md").read_text(encoding="utf-8"):
    external_blockers.append("final_reference_version_retraction_check")

# Prospective calibration is a scientific pending item, not a fatal flaw under current claims.
scientific_pending=["v24_prospective_N1_calibration"]
warnings.append("v24 completion is recommended before submission if operationally feasible; current manuscript must not claim field-wide calibration.")

technical_scope_pass=(len(errors)==0)
submission_ready=technical_scope_pass and len(external_blockers)==0 and len(scientific_pending)==0

result={
    "meta_reviewer":"A+B+C integrated",
    "status":"PASS" if technical_scope_pass else "FAIL",
    "meta_disposition":"PROCEED — NO FATAL TECHNICAL REJECTION REASON DETECTED FOR BOUNDED METHODS CLAIMS" if technical_scope_pass else "OPEN",
    "technical_scope_pass":technical_scope_pass,
    "submission_ready":submission_ready,
    "fatal_technical_rejection_reason_detected":not technical_scope_pass,
    "external_submission_blockers":external_blockers,
    "scientific_pending":scientific_pending,
    "warnings":warnings,
    "errors":errors,
    "reviewer_b_artifact_hashes":b_actual,
    "checks":checks,
}
OUT.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print(json.dumps({k:v for k,v in result.items() if k!="checks"},indent=2))
raise SystemExit(0 if technical_scope_pass else 1)
