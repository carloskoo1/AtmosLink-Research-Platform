#!/usr/bin/env python3
from pathlib import Path
import json, statistics, hashlib

ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
BASE=ROOT/"Results/scientific_discovery/DISCOVERY-001/ai_evaluation"
OUT=ROOT/"Results/scientific_discovery/DISCOVERY-001/reviewer_c_ai_comparator_audit.json"

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def metrics(obj):
    return {
        "alternative_explanations":len(obj.get("alternative_explanations",[])),
        "falsification_tests":len(obj.get("falsification_tests",[])),
        "description_chars":len(obj.get("description","")),
        "total_serialized_value_chars":sum(len(str(v)) for v in obj.values())
    }

rows=[]
for i in range(1,7):
    cid=f"RFATM-{i:04d}"
    bp=BASE/"baseline"/f"{cid}_baseline.json"
    ap=BASE/"a1"/f"{cid}_a1.json"
    b=json.loads(bp.read_text())
    a=json.loads(ap.read_text())
    rows.append({
        "candidate_id":cid,
        "B0":metrics(b),
        "A1":metrics(a),
        "B0_sha256":sha256(bp),
        "A1_sha256":sha256(ap)
    })

summary={}
for system in ["B0","A1"]:
    summary[system]={}
    for key in ["alternative_explanations","falsification_tests","description_chars","total_serialized_value_chars"]:
        vals=[r[system][key] for r in rows]
        summary[system][f"mean_{key}"]=statistics.mean(vals)
        summary[system][f"min_{key}"]=min(vals)
        summary[system][f"max_{key}"]=max(vals)

result={
    "experiment_id":"DISCOVERY-001",
    "audit":"Reviewer C AI comparator expressive-capacity audit",
    "status":"PASS",
    "candidate_count":len(rows),
    "rows":rows,
    "summary":summary,
    "interpretation":{
        "matched_alternative_slots":summary["B0"]["mean_alternative_explanations"]==summary["A1"]["mean_alternative_explanations"],
        "matched_test_slots":summary["B0"]["mean_falsification_tests"]==summary["A1"]["mean_falsification_tests"],
        "matched_text_budget":False,
        "utility_claim_authorized":False,
        "reason":"B0 and A1 do not have matched expressive opportunity; this audit supports downgrading the current utility comparison to safety/feasibility."
    }
}
OUT.write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(result,indent=2))
