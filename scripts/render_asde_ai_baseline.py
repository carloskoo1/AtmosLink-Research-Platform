#!/usr/bin/env python3
from pathlib import Path
import json,sys
ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
sys.path.insert(0,str(ROOT))
from scientific_discovery.ai_baseline_renderer import render

registry=json.loads((ROOT/"Results/scientific_discovery/DISCOVERY-001/candidate_registry.json").read_text())
outdir=ROOT/"Results/scientific_discovery/DISCOVERY-001/ai_evaluation/baseline"
outdir.mkdir(parents=True,exist_ok=True)
rows=[]
for c in registry["candidates"]:
    out=render(c)
    (outdir/f'{c["candidate_id"]}_baseline.json').write_text(json.dumps(out,indent=2)+"\n")
    rows.append(out)
(outdir/"baseline_all.json").write_text(json.dumps(rows,indent=2)+"\n")
print(f"rendered={len(rows)}")
