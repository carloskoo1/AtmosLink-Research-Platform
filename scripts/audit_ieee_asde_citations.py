#!/usr/bin/env python3
from pathlib import Path
import json

ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
DRAFT=ROOT/"docs/IEEE_ASDE_FULL_DRAFT_V1.md"
BIB=ROOT/"docs/IEEE_ASDE_REFERENCES_WORKING.bib"

draft=DRAFT.read_text(encoding="utf-8")
bib=BIB.read_text(encoding="utf-8")

keys=set()
for line in bib.splitlines():
    s=line.strip()
    if s.startswith("@") and "{" in s and "," in s:
        keys.add(s.split("{",1)[1].split(",",1)[0].strip())

used=set()
i=0
while True:
    a=draft.find("[",i)
    if a<0:
        break
    b=draft.find("]",a+1)
    if b<0:
        break
    group=draft[a+1:b]
    for raw in group.split(","):
        k=raw.strip()
        if k and k[0].isupper() and all(ch.isupper() or ch.isdigit() or ch=="-" for ch in k):
            used.add(k)
    i=b+1

missing=sorted(used-keys)
unused=sorted(keys-used)
result={
    "draft":str(DRAFT.relative_to(ROOT)),
    "bibliography":str(BIB.relative_to(ROOT)),
    "used_key_count":len(used),
    "bib_key_count":len(keys),
    "missing_from_bib":missing,
    "unused_bib":unused,
    "status":"PASS" if not missing else "FAIL"
}
out=ROOT/"Results/scientific_discovery/DISCOVERY-001/manuscript_v1_citation_audit.json"
out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print(json.dumps(result,indent=2))
raise SystemExit(0 if not missing else 1)
