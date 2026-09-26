#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,subprocess,sys
import numpy,pandas,scipy,matplotlib

ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
manifest=json.loads((ROOT/"scientific_discovery/environment_manifest.json").read_text())

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

errors=[]
snap=manifest["primary_development_snapshot"]
if sha256(ROOT/snap["path"])!=snap["sha256"]:
    errors.append("development snapshot SHA-256 mismatch")
protocol=manifest["v21_protocol"]
if sha256(ROOT/protocol["path"])!=protocol["sha256"]:
    errors.append("v21 protocol SHA-256 mismatch")

for name,expected in manifest["v21_artifacts"].items():
    path=ROOT/"Results/scientific_discovery/DISCOVERY-001/v21_end_to_end_audit"/name
    if sha256(path)!=expected:
        errors.append(f"{name} SHA-256 mismatch")

versions={
    "numpy":numpy.__version__,"pandas":pandas.__version__,
    "scipy":scipy.__version__,"matplotlib":matplotlib.__version__
}
for pkg,expected in manifest["packages"].items():
    if versions.get(pkg)!=expected:
        errors.append(f"{pkg} version {versions.get(pkg)} != recorded {expected}")

checks=[
    [sys.executable,str(ROOT/"scripts/verify_discovery_001_v21_audit.py")],
    [sys.executable,str(ROOT/"scripts/audit_discovery_holdout_isolation.py")],
]
outputs=[]
for cmd in checks:
    r=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
    outputs.append(r.stdout.strip())
    if r.returncode!=0:
        errors.append(f"verification command failed: {' '.join(cmd)}\n{r.stdout}\n{r.stderr}")

print("ASDE_PUBLICATION_ARTIFACT_VERIFICATION")
for o in outputs:
    if o: print(o)
if errors:
    print("STATUS=FAIL")
    for e in errors: print("ERROR:",e)
    raise SystemExit(1)
print("STATUS=PASS")
