#!/usr/bin/env python3
from pathlib import Path
import json,hashlib

ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
REG=ROOT/"Results/scientific_discovery/DISCOVERY-001/candidate_registry.json"
OUT=ROOT/"Results/scientific_discovery/DISCOVERY-001/ai_evaluation/packets"
OUT.mkdir(parents=True,exist_ok=True)

registry=json.loads(REG.read_text())
rows=[]
for c in registry["candidates"]:
    packet={
        "experiment_id":registry["experiment_id"],
        "candidate_id":c["candidate_id"],
        "status":c["status"],
        "pattern":c["pattern"],
        "failed_gate":c["failed_gate"],
        "reason":c["reason"],
        "validation_accessed":registry["validation_accessed"],
        "external_replication_accessed":registry["external_replication_accessed"]
    }
    raw=(json.dumps(packet,sort_keys=True,separators=(",",":"))+"\n").encode()
    sha=hashlib.sha256(raw).hexdigest()
    record={"packet":packet,"canonical_sha256":sha}
    (OUT/f'{c["candidate_id"]}_packet.json').write_text(json.dumps(record,indent=2)+"\n")
    rows.append(record)
(OUT/"packet_manifest.json").write_text(json.dumps(rows,indent=2)+"\n")
print(f"packets={len(rows)}")
