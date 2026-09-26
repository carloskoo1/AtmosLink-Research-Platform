#!/usr/bin/env python3
from pathlib import Path
import json,re

ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
DEV=ROOT/"Results/scientific_discovery/DISCOVERY-001/prevalidation_7000_20.csv"
ACTIVE=[
    ROOT/"scripts/run_discovery_001_v7_synthetic_benchmark.py",
    ROOT/"scripts/run_discovery_001_v8_detection_surface.py",
    ROOT/"scripts/run_discovery_001_v9_identifiability.py",
    ROOT/"scripts/run_discovery_001_v10_confirmatory_benchmark.py",
    ROOT/"scripts/run_discovery_001_v12_audit_confirmatory.py",
    ROOT/"scripts/run_discovery_001_v14_audit_ablation.py",
    ROOT/"scripts/run_discovery_001_v15_morphology_stress.py",
    ROOT/"scripts/run_discovery_001_v16_outcome_sensitivity.py",
    ROOT/"scripts/run_discovery_001_v16b_multiview_exploratory.py",
    ROOT/"scripts/run_discovery_001_v17_candidate_library_audit.py",
    ROOT/"scripts/run_discovery_001_v18_end_to_end_exploratory.py",
    ROOT/"scripts/run_discovery_001_v19_temporal_identifiability.py",
    ROOT/"scripts/run_discovery_001_v20_identifiability_tradeoff.py",
    ROOT/"scripts/run_discovery_001_v21_end_to_end_audit.py",
    ROOT/"scripts/run_discovery_001_v23_hidden_driver_gate_ablation.py",
]
FORBIDDEN=[
    "D_validation",
    "2026-09-13T03:34:50",
    "2026-09-16T03:51:31",
]
issues=[]
for path in ACTIVE:
    if not path.exists():
        issues.append({"file":str(path.relative_to(ROOT)),"issue":"missing"})
        continue
    text=path.read_text(encoding="utf-8")
    if "scientific_campaign_6g_integrated.csv" in text:
        issues.append({"file":str(path.relative_to(ROOT)),
                       "issue":"active analysis references full integrated source"})
    for token in FORBIDDEN:
        if token in text:
            issues.append({"file":str(path.relative_to(ROOT)),
                           "issue":f"contains holdout token {token}"})

result={
    "policy":"No D_validation values may be used for candidate selection, tuning, screening, benchmark calibration, or development evaluation.",
    "development_snapshot":str(DEV.relative_to(ROOT)),
    "active_scripts_checked":[str(p.relative_to(ROOT)) for p in ACTIVE],
    "issues":issues,
    "status":"PASS" if not issues else "FAIL",
    "scope_note":"This audit establishes analytical isolation of the active development pipeline. It does not claim that the original source file bytes were never read during historical partition construction."
}
out=ROOT/"Results/scientific_discovery/DISCOVERY-001/holdout_isolation_audit.json"
out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print(json.dumps(result,indent=2))
raise SystemExit(0 if not issues else 1)
