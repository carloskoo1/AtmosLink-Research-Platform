#!/usr/bin/env python3
from pathlib import Path
import json,hashlib,secrets,csv,os

ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
BASE=ROOT/"Results/scientific_discovery/DISCOVERY-001/ai_evaluation"
OUT=BASE/"blind_review"
OUT.mkdir(parents=True,exist_ok=True)
KEY=Path("/home/carlos/.asde_ai_pilot_review_key.json")

def normalize(x):
    def clean_test(s):
        if ":" in s:
            prefix,rest=s.split(":",1)
            if prefix.strip() in {
              "blocked_temporal_replication","same_clock_matched_control",
              "trend_diurnal_adjustment","event_refractory_independence",
              "strict_pre_post_directionality","post_event_negative_control",
              "outcome_definition_sensitivity","qc_feature_exclusion",
              "multiplicity_controlled_retest","prospective_new_data_replication"}:
                return rest.strip()
        return s
    return {
      "interpretation":x["description"],
      "alternative_explanations":x["alternative_explanations"],
      "falsification_tests":[clean_test(t) for t in x["falsification_tests"]],
      "recommended_action":x["recommended_action"]
    }

packets=json.loads((BASE/"packets/packet_manifest.json").read_text())
mapping={}
review=[]
for rec in packets:
    packet=rec["packet"]; cid=packet["candidate_id"]
    b=json.loads((BASE/"baseline"/f"{cid}_baseline.json").read_text())
    a=json.loads((BASE/"a1"/f"{cid}_a1.json").read_text())
    flip=bool(secrets.randbits(1))
    if flip:
        A,B=("A1",normalize(a)),("B0",normalize(b))
    else:
        A,B=("B0",normalize(b)),("A1",normalize(a))
    mapping[cid]={"option_A":A[0],"option_B":B[0]}
    review.append({
      "candidate_id":cid,
      "evidence":{
        "pattern":packet["pattern"],
        "failed_gate":packet["failed_gate"],
        "reason":packet["reason"],
        "status":packet["status"]
      },
      "option_A":A[1],
      "option_B":B[1]
    })

key_payload={"mapping":mapping}
key_raw=(json.dumps(key_payload,sort_keys=True,separators=(",",":"))+"\n").encode()
KEY.write_bytes(key_raw)
os.chmod(KEY,0o600)
key_sha=hashlib.sha256(key_raw).hexdigest()
(OUT/"review_items.json").write_text(json.dumps(review,indent=2)+"\n")
(OUT/"review_key_commitment.json").write_text(json.dumps({
  "key_sha256":key_sha,
  "key_location_during_blind_review":"outside repository",
  "reveal_policy":"Commit the exact key only after all reviewer forms are finalized.",
  "candidate_count":len(review)
},indent=2)+"\n")

fields=["candidate_id","reviewer_id",
"option_A_interpretive_completeness","option_A_alternative_usefulness",
"option_A_falsifiability","option_A_confounder_coverage","option_A_actionability",
"option_B_interpretive_completeness","option_B_alternative_usefulness",
"option_B_falsifiability","option_B_confounder_coverage","option_B_actionability",
"preferred_option","option_A_unsupported_speculation","option_B_unsupported_speculation",
"comments"]
with open(OUT/"review_form_template.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
    for item in review:
        w.writerow({"candidate_id":item["candidate_id"]})
print(f"review_items={len(review)}")
print(f"key_commitment_sha256={key_sha}")
