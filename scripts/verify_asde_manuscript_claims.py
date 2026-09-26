#!/usr/bin/env python3
from pathlib import Path
import json,re,math
import pandas as pd

ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
DRAFT=ROOT/"docs/IEEE_ASDE_FULL_DRAFT_V0.md"
text=DRAFT.read_text()
low=text.lower()

errors=[]

# Prohibited or overstrong wording.
prohibited={
    "first-claim":"asde is the first",
    "unique-claim":"asde is unique",
    "never-opened":"never opened",
    "never-read":"never read",
    "scientifically-proven":"scientifically proven",
    "natural-causality-weather-caused":"weather caused",
    "natural-causality-weather-causes":"weather causes",
}
for name,phrase in prohibited.items():
    if phrase in low:
        errors.append(f"{name}: prohibited phrase found: {phrase}")

# Current-state consistency.
if "rfatm-0006 is currently evidence_accumulating" in low:
    errors.append("stale RFATM-0006 status")
if "0 frozen natural hypotheses" not in low and "none reached the frozen-hypothesis state" not in low:
    errors.append("natural-hypothesis status not explicitly represented")

# Reconstruct primary known-driver benchmark.
v12=json.loads((ROOT/"Results/scientific_discovery/DISCOVERY-001/v12_audit/v12_summary.json").read_text())
if not math.isclose(v12["familywise_false_positive_rate"],0.025,abs_tol=1e-15):
    errors.append("v12 FPR source changed")
fr=pd.read_csv(ROOT/"Results/scientific_discovery/DISCOVERY-001/v12_audit/familywise_recovery.csv")
expected_v12={(0.5,15):1.00,(0.5,30):0.84,(0.5,60):0.62,
              (1.0,15):1.00,(1.0,30):1.00,(1.0,60):0.94}
for key,val in expected_v12.items():
    row=fr[(fr.effect_sd==key[0])&(fr.lag_min==key[1])]
    if len(row)!=1 or not math.isclose(float(row.familywise_recovery_rate.iloc[0]),val,abs_tol=1e-15):
        errors.append(f"v12 recovery mismatch {key}")

# Reconstruct primary hidden-driver claims.
v21=json.loads((ROOT/"Results/scientific_discovery/DISCOVERY-001/v21_end_to_end_audit/v21_summary.json").read_text())
if not math.isclose(v21["library_wide_null_fwer"],0.020,abs_tol=1e-15):
    errors.append("v21 null FWER source changed")
m=pd.read_csv(ROOT/"Results/scientific_discovery/DISCOVERY-001/v21_end_to_end_audit/end_to_end_metrics.csv")
for lag,truth,top in [(15,0.8525,0.945),(30,0.79,0.895),(60,0.2125,0.595)]:
    g=m[(m.scope=="aggregate")&(m.effect_sd==1.0)&(m.lag_min==lag)]
    gt=g[g.metric=="truth_selected"]
    gp=g[g.metric=="unique_top1_correct"]
    if len(gt)!=1 or not math.isclose(float(gt.rate.iloc[0]),truth,abs_tol=1e-15):
        errors.append(f"v21 truth-selected mismatch lag={lag}")
    if len(gp)!=1 or not math.isclose(float(gp.rate.iloc[0]),top,abs_tol=1e-15):
        errors.append(f"v21 top1 mismatch lag={lag}")

# Morphology claims.
v15=pd.read_csv(ROOT/"Results/scientific_discovery/DISCOVERY-001/v15_morphology_stress/morphology_recovery.csv")
for morph,vals in {
    "joint_step15":{15:1.00,30:1.00,60:0.98},
    "joint_ramp30":{15:1.00,30:1.00,60:0.77},
    "joint_sustained60":{15:1.00,30:1.00,60:0.98},
    "rssi_only_step15":{15:0.74,30:0.50,60:0.08},
    "snr_only_step15":{15:0.74,30:0.50,60:0.08},
    "mcs_only_step15":{15:0.74,30:0.50,60:0.08},
}.items():
    for lag,val in vals.items():
        row=v15[(v15.morphology==morph)&(v15.effect_sd==1.0)&(v15.lag_min==lag)]
        if len(row)!=1 or not math.isclose(float(row.recovery_rate.iloc[0]),val,abs_tol=1e-15):
            errors.append(f"v15 mismatch {morph}/{lag}")

# Basic draft presence checks for headline values.
required_strings=[
    "0.025","0.020","0.8525","0.7900","0.2125","0.9450","0.8950","0.5950",
    "six apparently promising atmospheric–rf candidates were screened out"
]
for s in required_strings:
    if s.lower() not in low:
        errors.append(f"draft missing required claim token: {s}")

print(f"draft_words={len(text.split())}")
print(f"errors={len(errors)}")
for e in errors:
    print("ERROR:",e)
if errors:
    raise SystemExit(1)
print("MANUSCRIPT_CLAIM_AUDIT_PASS")
