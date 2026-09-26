#!/usr/bin/env python3
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
import json,re,sys,pandas as pd

ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
DRAFT=ROOT/"docs/IEEE_ASDE_FULL_DRAFT_V1.md"
text=DRAFT.read_text(encoding="utf-8")

errors=[]
warnings=[]

# Forbidden or retired language.
for pat,msg in [
    (r"(?<!verification-)\b(first|novel|unprecedented)\s+(method|framework|workflow|system|approach|study)\b", "unqualified priority/novelty claim"),
    (r"\bnever opened\b", "overbroad holdout-access claim"),
    (r"\bnever read\b", "overbroad raw-byte access claim"),
    (r"validates a bounded discovery-and-screening process", "overstrong process-validation claim"),
    (r"recovered reliably", "overbroad reliability wording"),
    (r"immutable provenance", "overbroad provenance wording"),
    (r"the language model cannot hallucinate", "universal AI-safety claim"),
]:
    if re.search(pat,text,re.I):
        errors.append(msg)

# Headline v21 metrics must agree with stored audit artifacts.
metrics=pd.read_csv(ROOT/"Results/scientific_discovery/DISCOVERY-001/v21_end_to_end_audit/end_to_end_metrics.csv")
def rate(effect,lag,metric):
    g=metrics[(metrics["scope"]=="aggregate")&
              (metrics["effect_sd"]==effect)&
              (metrics["lag_min"]==lag)&
              (metrics["metric"]==metric)]
    if len(g)!=1:
        raise RuntimeError(f"metric lookup failed: {effect}/{lag}/{metric}")
    return float(g.iloc[0]["rate"])

expected={
    "85.3%":rate(1.0,15,"truth_selected"),
    "79.0%":rate(1.0,30,"truth_selected"),
    "21.3%":rate(1.0,60,"truth_selected"),
    "94.5%":rate(1.0,15,"unique_top1_correct"),
    "89.5%":rate(1.0,30,"unique_top1_correct"),
    "59.5%":rate(1.0,60,"unique_top1_correct"),
}
def pct_half_up(val):
    q=Decimal(str(val*100)).quantize(Decimal("0.1"),rounding=ROUND_HALF_UP)
    return f"{q}%"

for rendered,val in expected.items():
    target=pct_half_up(val)
    if rendered!=target:
        errors.append(f"hardcoded expected label {rendered} no longer matches artifact {target}")
    if rendered not in text:
        errors.append(f"headline v21 metric missing from draft: {rendered}")

# Check primary null FWER wording is present and bounded to the finite library.
if "library-wide null false-positive rate was 2.0%" not in text:
    errors.append("v21 library-wide null FWER not stated in Abstract")
if "four competing prespecified hypotheses" not in text:
    errors.append("finite hidden-driver library scope missing from Abstract")

# Known-driver headline values.
v12=json.loads((ROOT/"Results/scientific_discovery/DISCOVERY-001/v12_audit/v12_summary.json").read_text())
if abs(v12["familywise_false_positive_rate"]-0.025)>1e-12:
    errors.append("v12 FPR artifact changed")
for s in ["2.5%","94–100%"]:
    if s not in text:
        warnings.append(f"expected Abstract known-driver summary token absent: {s}")

# v23 hidden-driver gate ablation must remain correctly scoped.
v23dir=ROOT/"Results/scientific_discovery/DISCOVERY-001/v23_hidden_driver_gate_ablation"
v23metrics=pd.read_csv(v23dir/"gate_ablation_metrics.csv",keep_default_na=False)
def v23_fwer(method):
    g=v23metrics[(v23metrics["mode"]=="null")&
                 (v23metrics["metric"]=="library_wide_fwer")&
                 (v23metrics["method"]==method)]
    if len(g)!=1:
        raise RuntimeError(f"v23 FWER lookup failed: {method}")
    return float(g.iloc[0]["rate"])

if abs(v23_fwer("M0")-0.217)>1e-12:
    errors.append("v23 M0 FWER artifact changed")
for method in ["M1","M2","M3"]:
    if abs(v23_fwer(method)-0.017)>1e-12:
        errors.append(f"v23 {method} FWER artifact changed")

v23audit=json.loads((v23dir/"v23_reconstruction_audit.json").read_text())
if v23audit.get("m1_m2_m3_selected_sets_identical") is not True:
    errors.append("v23 M1/M2/M3 selected-set identity audit no longer passes")

for token in ["21.7%","1.7%","4,600 paired audit trials"]:
    if token not in text:
        errors.append(f"headline v23 token missing from draft: {token}")

if re.search(r"(full|complete)\s+(ASDE\s+)?gate.{0,80}(caused|accounted for).{0,80}(21\.7|1\.7)",text,re.I|re.S):
    errors.append("v23 improvement incorrectly attributed to the full gate")

# Holdout scope wording.
if "analytically isolated" not in text and "analytically embargoed" not in text:
    errors.append("holdout analytical-isolation language missing")

# Natural causality must remain explicitly disclaimed.
if "does not establish a natural atmospheric causal effect" not in text:
    errors.append("Abstract natural-causality disclaimer missing")

# AI incremental utility is still pending.
for m in re.finditer(r"AI (improves|enhances) scientific reasoning",text,re.I):
    context=text[max(0,m.start()-40):m.start()].lower()
    if "no claim that " not in context and "not establish that " not in context:
        errors.append("unauthorized AI incremental-value claim")

result={
    "draft":"IEEE_ASDE_FULL_DRAFT_V1.md",
    "status":"PASS" if not errors else "FAIL",
    "errors":errors,
    "warnings":warnings
}
out=ROOT/"Results/scientific_discovery/DISCOVERY-001/manuscript_v1_claim_audit.json"
out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print(json.dumps(result,indent=2))
raise SystemExit(0 if not errors else 1)
