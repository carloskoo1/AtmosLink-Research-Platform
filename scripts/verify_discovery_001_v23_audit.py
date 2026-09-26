#!/usr/bin/env python3
from pathlib import Path
import json, math, hashlib
import pandas as pd

ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
DIR=ROOT/"Results/scientific_discovery/DISCOVERY-001/v23_hidden_driver_gate_ablation"
PROTOCOL=ROOT/"docs/ASDE_HIDDEN_DRIVER_GATE_ABLATION_PROTOCOL.md"

EXPECTED_COMMIT="36d9f329b6e3f77ad9ec3546f2bde65428308eca"
EXPECTED_SOURCE_SHA="eed7df2621f6952b9ea2eaa7524f735a706b69494d3d272fd2dd828b52a97387"
EXPECTED_PROTOCOL_SHA="001857071d035e3bd5f30a5d3da5a2e3006cef5048d6394c32e4338b1ac2ebb7"

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

summary=json.loads((DIR/"v23_summary.json").read_text())
trials=pd.read_csv(DIR/"gate_ablation_trials.csv",keep_default_na=False)
metrics=pd.read_csv(DIR/"gate_ablation_metrics.csv",keep_default_na=False)

errors=[]
if summary["protocol_git_commit"]!=EXPECTED_COMMIT:
    errors.append("protocol_git_commit mismatch")
if summary["development_snapshot_sha256"]!=EXPECTED_SOURCE_SHA:
    errors.append("development snapshot SHA mismatch")
if summary["protocol_sha256"]!=EXPECTED_PROTOCOL_SHA:
    errors.append("protocol SHA mismatch")
if sha256(PROTOCOL)!=EXPECTED_PROTOCOL_SHA:
    errors.append("current protocol file SHA mismatch")
if summary["validation_accessed"] is not False:
    errors.append("validation_accessed is not false")
if summary["external_replication_accessed"] is not False:
    errors.append("external_replication_accessed is not false")

inj=trials[trials["mode"]=="injected"]
nul=trials[trials["mode"]=="null"]
if len(trials)!=18400 or len(inj)!=14400 or len(nul)!=4000:
    errors.append(f"unexpected trial counts total/inj/null={len(trials)}/{len(inj)}/{len(nul)}")

methods=sorted(trials["method"].unique())
if methods!=["M0","M1","M2","M3"]:
    errors.append(f"unexpected methods {methods}")

def fwer(method):
    g=nul[nul["method"]==method]
    return float((pd.to_numeric(g["n_selected"])>0).mean())

expected_fwer={"M0":0.217,"M1":0.017,"M2":0.017,"M3":0.017}
for method,expected in expected_fwer.items():
    got=fwer(method)
    if not math.isclose(got,expected,abs_tol=1e-15):
        errors.append(f"{method} FWER {got} != {expected}")

keys=["mode","truth_driver","effect_sd","lag_min","seed"]
wide=trials.pivot(index=keys,columns="method",values="selected_drivers").reset_index()
for pair in [("M1","M2"),("M1","M3"),("M2","M3")]:
    n=int((wide[pair[0]]!=wide[pair[1]]).sum())
    if n!=0:
        errors.append(f"{pair[0]} vs {pair[1]} differ in {n} trials")

def asbool(s):
    if s.dtype==bool:
        return s
    return s.astype(str).str.lower().eq("true")

inj=inj.copy()
inj["truth_bool"]=asbool(inj["truth_selected"])
inj["dist_bool"]=asbool(inj["distractor_coselected"])
inj["exclusive"]=inj["truth_bool"] & ~inj["dist_bool"]

expected_exclusive={
    ("M0",15):0.4250,("M1",15):0.8500,
    ("M0",30):0.2400,("M1",30):0.8175,
    ("M0",60):0.0925,("M1",60):0.2100,
}
for (method,lag),expected in expected_exclusive.items():
    g=inj[(inj["method"]==method)&
          (pd.to_numeric(inj["effect_sd"])==1.0)&
          (pd.to_numeric(inj["lag_min"])==lag)]
    got=float(g["exclusive"].mean())
    if not math.isclose(got,expected,abs_tol=1e-15):
        errors.append(f"exclusive {method}/{lag}: {got} != {expected}")

for method in ["M1","M2","M3"]:
    g=inj[inj["method"]==method]
    if int(g["dist_bool"].sum())!=0:
        errors.append(f"{method} has injected distractor co-selections")

result={
    "experiment_id":"DISCOVERY-001",
    "audit":"v23 hidden-driver gate ablation reconstruction",
    "status":"PASS" if not errors else "FAIL",
    "trial_counts":{"total":len(trials),"injected":len(inj),"null":len(nul)},
    "null_fwer":{m:fwer(m) for m in methods},
    "m1_m2_m3_selected_sets_identical":not any(" vs " in e for e in errors),
    "errors":errors
}
(DIR/"v23_reconstruction_audit.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(result,indent=2))
raise SystemExit(0 if not errors else 1)
